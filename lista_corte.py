# SPDX-License-Identifier: GPL-3.0-or-later
"""IngeTrazo: lista de corte para marcenaria (plugin de arquivo único).

Instale este arquivo na pasta aberta por Extensions > Open plugins folder.
Compatível com a API de ferramentas descrita em docs/plugins.md (série 0.x).
Não modifica o modelo. Medidas em milímetros; a cena usa metros.
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from dataclasses import dataclass

from tools.base import Tool


@dataclass
class Piece:
    name: str
    qty: int
    length: float  # mm
    width: float   # mm
    thickness: float  # mm
    issue: str = ""

    @property
    def area(self):
        return self.qty * self.length * self.width / 1_000_000.0


# Pure geometry functions, testable without a Qt event loop.
def _xyz(point):
    return (float(point.x()), float(point.y()), float(point.z()))


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _size(a):
    return math.sqrt(_dot(a, a))


def _as_local(group, matrix):
    """Return coordinates in group axes and three physical axis scales.

    A classic group keeps world-space geometry and its axes separately;
    component instances instead keep prototype-local geometry. We must
    not use a world AABB for a rotated board.
    """
    axes = getattr(group, "axes", None)
    vertices = group.mesh.vertices
    if axes is not None:
        inv, ok = axes.inverted()  # QMatrix4x4.inverted -> (matrix, bool)
        if not ok:
            raise ValueError("eixos do grupo não invertíveis")
        coords = [_xyz(inv.map(v.position)) for v in vertices]
        basis = matrix * axes if matrix is not None else axes
    else:
        coords = [_xyz(v.position) for v in vertices]
        basis = matrix

    if basis is None:
        return coords, (1.0, 1.0, 1.0), ""

    from PySide6.QtGui import QVector3D
    o = basis.map(QVector3D(0, 0, 0))
    vecs = []
    for unit in (QVector3D(1, 0, 0), QVector3D(0, 1, 0), QVector3D(0, 0, 1)):
        vecs.append(_xyz(basis.map(unit) - o))
    scales = [_size(v) for v in vecs]
    if min(scales) <= 1e-9:
        raise ValueError("transformação com escala zero")
    norms = [tuple(x/s for x in v) for x, s in zip(vecs, scales)]
    shear = any(abs(_dot(norms[i], norms[j])) > 0.002
                for i, j in ((0, 1), (0, 2), (1, 2)))
    return coords, tuple(scales), ("Transformação com cisalhamento" if shear else "")


def _poly_area_2d(pts, i, j):
    return abs(sum(pts[k][i] * pts[(k+1) % len(pts)][j]
                   - pts[(k+1) % len(pts)][i] * pts[k][j]
                   for k in range(len(pts)))) * 0.5


def _rectangular_solid(group, coords, mins, maxs):
    """Conservatively validate a six-sided, axis-aligned solid.

    Faces may subdivide a side. Disallow holes, internal/diagonal faces,
    missing sides and irregular outlines. Validity is NOT a nesting test.
    """
    faces = group.mesh.faces
    if not faces:
        return False
    span = [maxs[i]-mins[i] for i in range(3)]
    if min(span) <= 1e-8:
        return False

    # Locate vertices by identity, to preserve loops with shared vertices.
    vertex_to_coord = {id(v): p for v, p in zip(group.mesh.vertices, coords)}
    areas = defaultdict(float)
    for face in faces:
        if getattr(face, "hole_loops", None) or getattr(face, "interior", False):
            return False
        pts = [vertex_to_coord.get(id(v)) for v in face.loop]
        if len(pts) < 3 or any(p is None for p in pts):
            return False
        planes = []
        for axis in range(3):
            tol = max(span[axis] * 1e-5, 5e-6)  # metres; 0.005mm minimum
            if all(abs(p[axis] - mins[axis]) <= tol for p in pts):
                planes.append((axis, 0))
            if all(abs(p[axis] - maxs[axis]) <= tol for p in pts):
                planes.append((axis, 1))
        if len(planes) != 1:
            return False
        axis, side = planes[0]
        a, b = [i for i in range(3) if i != axis]
        areas[(axis, side)] += _poly_area_2d(pts, a, b)
    for axis in range(3):
        a, b = [i for i in range(3) if i != axis]
        expected = span[a] * span[b]
        for side in (0, 1):
            if abs(areas[(axis, side)] - expected) > max(expected * 0.015, 1e-9):
                return False
    return True


def _visible(scene, group):
    visible = getattr(scene, "entity_visible", None)
    return bool(visible(group)) if callable(visible) else not getattr(group, "hidden", False)


def collect_pieces(scene):
    """Report one independent piece per non-empty placed GROUP mesh.

    Nested placements are visited once and transformed through ancestors.
    Loose geometry is never assumed to be a physical panel.
    """
    out = []
    skipped = {"empty": 0, "hidden": 0, "billboard": 0, "loose": 0}
    loose = scene.loose_mesh
    skipped["loose"] = len(loose.faces) if loose is not None else 0

    def walk(g, base=None, prefix=""):
        if not _visible(scene, g):
            skipped["hidden"] += 1
            return
        if getattr(g, "billboard", False):
            skipped["billboard"] += 1
            return
        own = getattr(g, "xform", None)
        transform = (base * own if base is not None and own is not None
                     else (own if own is not None else base))
        full_name = (prefix + " / " if prefix else "") + (g.name or "Peça")
        if g.mesh.vertices and g.mesh.faces:
            try:
                coords, scales, warning = _as_local(g, transform)
                mins = [min(p[i] for p in coords) for i in range(3)]
                maxs = [max(p[i] for p in coords) for i in range(3)]
                dims = sorted(((maxs[i] - mins[i]) * scales[i] * 1000
                               for i in range(3)), reverse=True)
                notices = []
                if warning:
                    notices.append(warning)
                if not _rectangular_solid(g, coords, mins, maxs):
                    notices.append("REVISAR: sólido não retangular (caixa envolvente)")
                if dims[2] < 0.2:
                    notices.append("REVISAR: espessura inferior a 0,2 mm")
                if dims[2] > 80:
                    notices.append("REVISAR: espessura superior a 80 mm")
                # Zero-size / degenerate solids are never useful cut pieces.
                if min(dims) > 0:
                    out.append(Piece(full_name, 1,
                                     *dims, "; ".join(notices)))
                else:
                    skipped["empty"] += 1
            except (ValueError, ArithmeticError, AttributeError, TypeError) as exc:
                out.append(Piece(full_name, 1, 0, 0, 0,
                                 "REVISAR: impossível medir — " + str(exc)))
        elif g.mesh.vertices or g.mesh.edges:
            skipped["empty"] += 1
        for child in getattr(g, "children", ()) or ():
            walk(child, transform, full_name)

    for group in scene.groups:
        walk(group)
    return out, skipped


def group_pieces(pieces):
    """Group matching validated panels while retaining their source names.

    Irregular panels never silently merge. Materials are not considered.
    Comparisons at 0.1 mm resolution; exports also use 0.1 mm.
    """
    grouped = {}
    for seq, p in enumerate(pieces):
        dims = (round(p.length, 1), round(p.width, 1), round(p.thickness, 1))
        bad = bool(p.issue)  # Keep anything with doubts separate.
        key = (dims, seq if bad else None)
        if key not in grouped:
            grouped[key] = Piece(p.name, p.qty, *dims, p.issue)
        else:
            old = grouped[key]
            old.qty += p.qty
            names = old.name.split(" | ")
            if p.name not in names:
                old.name += " | " + p.name
    return sorted(grouped.values(), key=lambda p: (
        -p.thickness, -p.length, -p.width, p.name.lower()))


def _number(value, decimals=1):
    return f"{value:.{decimals}f}".replace(".", ",")


def _safe_csv(text):
    """Prevent formula execution in Excel/LibreOffice when opening CSV."""
    val = str(text).strip()
    if val.startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + val
    return val


def make_csv(path, rows):
    """Write semicolon-separated, UTF-8 BOM CSV (Brazilian Excel friendly).

    rows: list of (description, qty, length, width, thickness,
                  edge_long, edge_short, issue).
    """
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        w = csv.writer(file, delimiter=";")
        w.writerow(["Peça / localização", "Quantidade",
                    "Comprimento (mm)", "Largura (mm)", "Espessura (mm)",
                    "Fita borda: lados longos (0-2)",
                    "Fita borda: lados curtos (0-2)",
                    "Área total (m²)", "Fita total (m)", "Observações"])
        for name, qty, length, width, thickness, edge_a, edge_b, issue in rows:
            area = qty*length*width/1e6
            tape = qty*(edge_a*length+edge_b*width)/1000
            w.writerow([_safe_csv(name), qty,
                        _number(length), _number(width), _number(thickness),
                        edge_a, edge_b, _number(area, 3), _number(tape, 3),
                        _safe_csv(issue)])


def _show_dialog(viewport):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QBrush, QColor
    from PySide6.QtWidgets import (
        QApplication, QAbstractItemView, QCheckBox, QDialog, QFileDialog,
        QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton,
        QTableWidget, QTableWidgetItem, QVBoxLayout,
    )

    dialog = QDialog(viewport.window())
    dialog.setWindowTitle("Lista de corte — Marcenaria | IngeTrazo")
    dialog.resize(1100, 620)
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel(
        "Cada grupo/componente com geometria representa uma peça. "
        "Medidas reais em mm; dimensões C × L × E, da maior para a menor."))
    status = QLabel("")
    status.setWordWrap(True)
    layout.addWidget(status)
    table = QTableWidget()
    headers = ["Peça / localização", "Qtde", "Comp. (mm)",
               "Larg. (mm)", "Esp. (mm)", "Fita C", "Fita L",
               "Área (m²)", "Observações"]
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    table.horizontalHeader().setStretchLastSection(True)
    table.setColumnWidth(0, 210)
    table.setColumnWidth(8, 260)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSortingEnabled(False)
    layout.addWidget(table, 1)
    layout.addWidget(QLabel(
        "Fita C = quantidade de lados com fita paralelos ao comprimento (0–2). "
        "Fita L = lados paralelos à largura (0–2). Você pode editar o nome das peças. "
        "Essas alterações não são gravadas no modelo."))
    export_irregular = QCheckBox(
        "Incluir também peças com AVISOS na exportação (exige conferência manual)")
    export_irregular.setChecked(False)
    layout.addWidget(export_irregular)
    buttons = QHBoxLayout()
    refresh_btn = QPushButton("Atualizar do modelo")
    export_btn = QPushButton("Exportar CSV…")
    copy_btn = QPushButton("Copiar tabela")
    close_btn = QPushButton("Fechar")
    for btn in (refresh_btn, copy_btn, export_btn, close_btn):
        buttons.addWidget(btn)
    layout.addLayout(buttons)

    def fill():
        pieces, skipped = collect_pieces(viewport.scene)
        groups = group_pieces(pieces)
        table.setRowCount(len(groups))
        for i, piece in enumerate(groups):
            cells = [piece.name, str(piece.qty),
                     _number(piece.length), _number(piece.width),
                     _number(piece.thickness), "0", "0",
                     _number(piece.area, 3), piece.issue]
            for j, val in enumerate(cells):
                item = QTableWidgetItem(val)
                if j not in (0, 5, 6):
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if j in (1, 2, 3, 4, 5, 6, 7):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if piece.issue:
                    item.setBackground(QBrush(QColor("#FFF1C7")))
                    if j == 8:
                        item.setToolTip(piece.issue)
                table.setItem(i, j, item)
        bad = sum(1 for p in groups if p.issue)
        status.setText(
            f"{len(pieces)} peças encontradas, {len(groups)} linhas agrupadas; "
            f"área total { _number(sum(p.area for p in pieces), 3) } m². "
            f"{bad} linha(s) com avisos. "
            f"Geometria solta ignorada: {skipped['loose']} face(s); "
            f"ocultos ignorados: {skipped['hidden']}; "
            f"objetos sem sólido: {skipped['empty']}.")
        export_btn.setEnabled(bool(groups))
        copy_btn.setEnabled(bool(groups))

    def extract_rows():
        rows = []
        omitted = 0
        for i in range(table.rowCount()):
            vals = [table.item(i, j).text().strip() for j in range(9)]
            if vals[8] and not export_irregular.isChecked():
                omitted += 1
                continue
            try:
                qty = int(vals[1])
                dims = [float(vals[j].replace(",", ".")) for j in (2, 3, 4)]
                edges = [int(vals[j]) for j in (5, 6)]
            except ValueError as exc:
                raise ValueError(f"Linha {i+1}: número inválido") from exc
            if qty < 1 or any(d <= 0 for d in dims):
                raise ValueError(f"Linha {i+1}: dimensões e quantidade devem ser positivas")
            if any(v not in (0, 1, 2) for v in edges):
                raise ValueError(f"Linha {i+1}: Fita C e Fita L devem ser 0, 1 ou 2")
            rows.append((vals[0], qty, *dims, *edges, vals[8]))
        return rows, omitted

    def export():
        try:
            rows, omitted = extract_rows()
            if not rows:
                QMessageBox.warning(dialog, "Lista de corte", "Nenhuma peça válida para exportar.")
                return
            path, _ = QFileDialog.getSaveFileName(
                dialog, "Salvar lista de corte", "lista_de_corte.csv", "CSV (*.csv)")
            if not path:
                return
            if not path.lower().endswith(".csv"):
                path += ".csv"
            make_csv(path, rows)
            QMessageBox.information(
                dialog, "Lista de corte",
                f"Lista exportada para:\n{path}\n\n"
                f"{len(rows)} linhas exportadas; {omitted} com avisos não exportadas.\n"
                "Revise medidas e acabamento antes de cortar.")
        except (ValueError, OSError) as exc:
            QMessageBox.critical(dialog, "Erro na exportação", str(exc))

    def copy():
        try:
            rows, omitted = extract_rows()
            if not rows:
                QMessageBox.warning(dialog, "Lista de corte", "Não há linhas válidas para copiar.")
                return
            header = ["Peça", "Qtde", "Comprimento (mm)",
                      "Largura (mm)", "Espessura (mm)", "Fita C", "Fita L", "Observações"]
            lines = ["\t".join(header)]
            for r in rows:
                lines.append("\t".join(_safe_csv(str(v)) for v in r))
            QApplication.clipboard().setText("\n".join(lines))
            status.setText(status.text() + f" | Copiado: {len(rows)} linhas, {omitted} omitidas.")
        except ValueError as exc:
            QMessageBox.warning(dialog, "Lista de corte", str(exc))

    refresh_btn.clicked.connect(fill)
    export_btn.clicked.connect(export)
    copy_btn.clicked.connect(copy)
    close_btn.clicked.connect(dialog.accept)
    fill()
    dialog.exec()


class ListaCorteMarcenaria(Tool):
    name = "Lista de corte — Marcenaria"
    shortcut = None
    description = "Agrupa peças de madeira e exporta lista de corte CSV em mm."
    uses_snap = False

    def on_activate(self, viewport):
        _show_dialog(viewport)

    def on_deactivate(self, viewport):
        pass
