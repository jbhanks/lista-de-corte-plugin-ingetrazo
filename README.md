# Lista de Corte / Cutting List / Lista de Corte — IngeTrazo

**Plugin gratuito de marcenaria / Free woodworking plugin / Extensión gratuita de carpintería**

[Português](#português) · [Español](#español) · [English](#english)

> **Status / Estado / Status — v1.0.0:** plugin testado pelo autor em uma instalação real do IngeTrazo e confirmado em funcionamento.
>
> Probado por el autor en una instalación real de IngeTrazo y confirmado en funcionamiento.
>
> Tested by the author in a real IngeTrazo installation and confirmed working.

---

## Português

### O que faz

O **Lista de Corte — Marcenaria** lê grupos e componentes de um projeto no [IngeTrazo](https://github.com/ingelibre/ingetrazo) para criar uma lista de peças destinadas à fabricação de móveis.

- Mede **comprimento, largura e espessura** em milímetros, considerando a orientação e escala dos componentes.
- **Agrupa peças de dimensões idênticas** (resolução de 0,1 mm) e calcula quantidades e áreas.
- Permite editar os **nomes das peças** e informar **0, 1 ou 2 lados** com fita de borda em cada direção.
- Calcula a metragem de fita e exporta o relatório em **CSV**, com ponto e vírgula, separador decimal por vírgula e UTF-8 BOM (adequado ao Excel em português).
- Marca peças que não correspondem a sólidos retangulares confiáveis como **REVISAR**, deixando-as fora da exportação por padrão.
- **Não inclui materiais** na tabela nem no CSV.

### Como instalar

1. Baixe o arquivo [`lista_corte.py`](lista_corte.py).
2. No IngeTrazo, abra **Extensions → Open plugins folder**.
3. Copie `lista_corte.py` para a pasta aberta e reinicie o aplicativo.
4. Abra seu projeto e selecione **Extensions → Lista de corte — Marcenaria**.

Pastas padrão: Windows `%APPDATA%\ingetrazo\plugins\`; Linux `~/.local/share/ingetrazo/plugins/` (respeitando `XDG_DATA_HOME`). O plugin não precisa de dependências adicionais além das distribuídas com o próprio IngeTrazo.

### Como preparar o desenho

Crie **um grupo ou componente por peça física** (lateral, base, porta, prateleira). Dê nomes claros às peças. Instâncias repetidas são contabilizadas separadamente; grupos aninhados são percorridos. A geometria solta, fora de grupos, não entra na lista. Um único grupo contendo várias chapas não é dividido automaticamente em peças.

Na janela, ajuste o nome e as colunas **Fita C** (bordas paralelas ao comprimento) e **Fita L** (bordas paralelas à largura), depois clique em **Exportar CSV** ou **Copiar tabela**. A edição não altera o arquivo `.igz`.

**Importante:** comprimento, largura e espessura são, respectivamente, as três dimensões da caixa geométrica **da maior para a menor**; a menor dimensão é presumida como espessura. Confira a orientação do veio, a espessura efetiva, fita, tolerâncias e folgas antes de cortar qualquer peça. O plugin **não otimiza o aproveitamento de chapas**, não calcula kerf, cortes inclinados, furos nem usinagens.

---

## Español

### Funciones

**Lista de Corte — Marcenaria** genera un despiece para la fabricación de muebles a partir de los grupos y componentes de un modelo de [IngeTrazo](https://github.com/ingelibre/ingetrazo).

- Calcula **largo, ancho y espesor** en milímetros, incluyendo orientación y escala de componentes.
- **Agrupa piezas con las mismas dimensiones** (precisión de 0,1 mm) y calcula cantidades y superficie.
- Permite editar la **descripción** y definir **0, 1 o 2 cantos** para cada dirección.
- Calcula la longitud total del tapacanto y exporta un **CSV** separado por punto y coma, con decimales mediante coma y codificación UTF-8 BOM.
- Advierte si un objeto no es un sólido rectangular fiable (**REVISAR**) y lo excluye de la exportación de forma predeterminada.
- **No incluye el material** en la tabla ni en el CSV.

### Instalación

1. Descargue [`lista_corte.py`](lista_corte.py).
2. En IngeTrazo, abra **Extensions → Open plugins folder**.
3. Copie `lista_corte.py` en la carpeta y reinicie IngeTrazo.
4. Abra un modelo y seleccione **Extensions → Lista de corte — Marcenaria**.

Carpetas habituales: Windows `%APPDATA%\ingetrazo\plugins\`; Linux `~/.local/share/ingetrazo/plugins/` (respeta `XDG_DATA_HOME`). No se necesitan dependencias adicionales fuera de las incluidas en IngeTrazo.

### Preparación y uso

Modele **cada tablero como un grupo o componente independiente**: lateral, estante, puerta, fondo, etc. Las instancias repetidas y los grupos anidados se recorren; la geometría suelta no se incluye. Un grupo con varios tableros no se separa automáticamente.

En la ventana, puede editar la descripción y las columnas **Fita C** (cantos paralelos al largo) y **Fita L** (cantos paralelos al ancho), luego **Exportar CSV** o **Copiar tabela**. Los cambios no modifican el `.igz`.

**Atención:** las tres dimensiones se ordenan de mayor a menor, por lo que se supone que la más pequeña es el espesor. Verifique veta, espesor real, cantos y tolerancias antes de fabricar. **No es un optimizador de tableros**: no calcula el ancho de la sierra, perforaciones, mecanizados ni despiece anidado.

---

## English

### Features

**Lista de Corte — Marcenaria** generates a woodworking cut list from groups and components in an [IngeTrazo](https://github.com/ingelibre/ingetrazo) model.

- Measures **length, width and thickness** in millimetres, accounting for component orientation and scale.
- **Groups identical dimensions** (0.1 mm precision) and totals quantities and panel area.
- Lets you edit **part names** and enter **0, 1 or 2 edge-banded sides** along each direction.
- Calculates total edge banding length and exports an **Excel-friendly CSV** (semicolon delimiter, comma decimals, UTF-8 BOM).
- Flags geometry that is not a reliable rectangular solid as **REVISAR** (“check manually”) and excludes it from exports by default.
- **Does not include a material field** in the table or CSV.

### Installation

1. Download [`lista_corte.py`](lista_corte.py).
2. In IngeTrazo, open **Extensions → Open plugins folder**.
3. Copy `lista_corte.py` into that folder and restart IngeTrazo.
4. Open a model, then use **Extensions → Lista de corte — Marcenaria**.

Default locations: Windows `%APPDATA%\ingetrazo\plugins\`; Linux `~/.local/share/ingetrazo/plugins/` (honours `XDG_DATA_HOME`). No extra dependencies beyond those bundled with IngeTrazo are required.

### Model preparation and usage

Model **one physical board per group or component** (side, shelf, door, back panel, etc.). Repeated instances are counted individually and nested groups are traversed. Ungrouped geometry is ignored; multiple boards combined in one group will not be split into separate parts automatically.

In the dialog, edit the part name and **Fita C** (edges parallel to the length) and **Fita L** (edges parallel to the width). Then select **Exportar CSV** (export CSV) or **Copiar tabela** (copy table). These edits do not change the `.igz` model.

**Production warning:** the plugin sorts the three geometric dimensions from largest to smallest and assumes the shortest is the thickness. Always verify the actual stock thickness, grain direction, banding, clearances and machining requirements before cutting. This **is not a sheet nesting optimizer** and does not calculate kerf, drilling, machining or optimal panel layouts.

---

## License / Licença / Licencia

[GPL-3.0-or-later](LICENSE). Based on the [IngeTrazo plugin API documentation](https://github.com/ingelibre/ingetrazo/blob/main/docs/plugins.md). Contributions and issue reports are welcome through this repository.