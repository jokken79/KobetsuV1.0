# Especificaciones de Templates - Formatos de Documentos
## UNS Kobetsu Keiyakusho - Análisis de Formatos Excel

Generado: 2025-11-26
Fuente: `個別契約書TEXPERT2025.7PerfectSin nada .xlsx`

---

## 📋 Resumen de Documentos a Implementar

| # | Documento | Área Impresión | Orient. | Papel | Escala | Prioridad |
|---|-----------|----------------|---------|-------|--------|-----------|
| 1 | 個別契約書X | A1:AA64 | Portrait | A4 (9) | 96% | ✅ ALTA |
| 2 | 通知書 | H1:P66 | Portrait | A4 (9) | 70% | ✅ ALTA |
| 3 | DAICHO | A1:BE78 | Portrait | A4 (9) | Auto | ✅ ALTA |
| 4 | 派遣元管理台帳 | A1:AB71 | Portrait | A4 (9) | 94% | 🔄 MEDIA |
| 5 | 就業条件明示書 | A1:AA56 | Portrait | A4 (9) | 95% | 🔄 MEDIA |
| 6 | 就業状況報告書 | A1:AI35 | Landscape | A4 (9) | Auto | ⏳ BAJA |
| 7 | 契約書 | A1:R54 | Landscape | A4 (9) | 70% | ⏳ BAJA |
| 8 | 雇入れ時の待遇情報 | Toda hoja | Portrait | A4 (9) | Auto | ⏳ BAJA |

---

## 1. 📄 個別契約書X (Contrato Individual de派遣)

### Información Técnica
```yaml
Nombre: 人材派遣個別契約書
Área de impresión: A1:AA64 (27 columnas x 64 filas)
Orientación: Portrait (vertical)
Tamaño papel: A4 (9)
Escala: 96%
Márgenes: Estándar Excel
Estado actual: ✅ IMPLEMENTADO en web (backend/app/services/kobetsu_pdf_service.py)
```

### Estructura del Documento

#### **Sección 1: Encabezado (Filas 1-3)**
```
Fila 1:  [Centrado] 人材派遣個別契約書
Fila 2:  [Texto introductorio] 加藤木材工業株式会社（以下、「甲」という）と...
Fila 3:  [Vacía]
```

#### **Sección 2: Información de派遣先 (Cliente) - Filas 4-9**
```
Fila 4:  派遣先 | 派遣先事業所 | 名称: [加藤木材工業株式会社] | 所在地: [...]
Fila 5:  　　　 | 就業場所     | 名称: [加藤木材工業株式会社 本社工場] | 所在地: [...]
Fila 6:         |              | 組織単位: [生産1部 2課]
Fila 7:         | 電話番号: [0568-81-7111]
Fila 8:         | 製造業務専門派遣先責任者 | 部署: [生産統括部] | 役職: [部長] | 氏名: [渡邉　茂芳]
Fila 9:         | 　　　　　　　　　　　　 | 連絡先: [0568-81-7111]
```

**Datos dinámicos:**
- `派遣先名`: Nombre de la empresa cliente (company_name)
- `就業場所`: Nombre específico de la planta/fábrica (factory_name)
- `組織単位`: Departamento + Línea (department + line)
- `責任者`: Supervisor responsable (supervisor_name, supervisor_department)

#### **Sección 3: Información de派遣元 (UNS企画) - Filas 10-11**
```
Fila 10: 派遣元 | 製造業務専門派遣元責任者 | 部署: [営業部] | 役職: [...] | 氏名: [...]
Fila 11:        | 連絡先: [...]
```

**Datos estáticos de UNS企画:**
- Nombre: ユニバーサル企画株式会社
- Dirección: 愛知県名古屋市...
- 派遣番号: 派13-123456

#### **Sección 4: Contenido de派遣 - Filas 12-15**
```
Fila 12: 派遣内容 | 派遣労働者を協定対象労働者に限定するか否か: [限定しない]
Fila 13:          | 業務内容: [生産設備稼動（製造・組立・補助）]
Fila 14:          | 派遣労働者の責任の程度: [通常業務]
Fila 15:          | 指揮命令者: 部署 [生産1部] 役職 [課長] 氏名 [...]
```

**Datos dinámicos:**
- `業務内容`: work_content
- `責任の程度`: responsibility_level ("補助的業務" / "通常業務" / "責任業務")
- `指揮命令者`: command_supervisor_*

#### **Sección 5: Período y Horario - Filas 16-19**
```
Fila 16: 派遣期間: [2025-02-17] ～ [2025-09-30] | 人数: [名]
Fila 17: 派遣労働者氏名: [別紙参照]
Fila 18: 就業時間: 昼勤：8時00分～17時00分 ・ 夜勤：20時00分～5時00分 (実働　7時間40分）
Fila 19: 就業日: [月曜日から金曜日まで（会社カレンダーによる）]
```

**Datos dinámicos:**
- `dispatch_start_date`, `dispatch_end_date`
- `work_start_time`, `work_end_time`, `break_minutes`
- `working_days`: Array de días seleccionados

#### **Sección 6: Tarifas (派遣料金) - Filas 20-35**
```
Fila 20: 派遣料金 | 基本時間の単価: 1時間あたり¥1,800
Fila 21-30: [Tabla de tarifas por tiempo extra con fórmulas]
```

**Cálculos importantes:**
```
基本時間単価: hourly_rate (ej: ¥1,800)
割増時間単価 (25%): hourly_rate * 1.25 (ej: ¥2,250)
割増時間単価 (35%): hourly_rate * 1.35 (ej: ¥2,430)
割増時間単価 (50%): hourly_rate * 1.50 (ej: ¥2,700)
割増時間単価 (60時間超): hourly_rate * 1.50 (ej: ¥2,700)
```

#### **Sección 7: Términos Legales - Filas 35-55**
```
Texto legal extenso sobre:
1. 労働者派遣法
2. 派遣労働者の特定目的
3. 損害賠償
4. 苦情処理
5. その他
```

**Importante:** Este texto es principalmente estático, pero puede tener campos variables.

#### **Sección 8: Firmas - Filas 56-64**
```
Fila 60: （甲）                                  （乙）
Fila 61: 加藤木材工業株式会社                    ユニバーサル企画株式会社
Fila 62: 住所: [...]                             住所: 461-0025
Fila 63: 代表者: [...]                           代表者: 杉浦　準
Fila 64: 印                                      印
```

### Estado de Implementación
✅ **YA IMPLEMENTADO** en `backend/app/services/kobetsu_pdf_service.py`

**Archivos relacionados:**
- Template: `backend/templates/kobetsu_template.docx`
- Service: `backend/app/services/kobetsu_pdf_service.py`
- API: `backend/app/api/v1/endpoints/kobetsu.py` → `/kobetsu/{id}/generate-pdf`

**Mejoras necesarias:**
1. ⚠️ Verificar que el layout coincida 100% con el Excel
2. ⚠️ Añadir la tabla de tarifas calculada
3. ⚠️ Validar márgenes y espaciado
4. ⚠️ Verificar texto legal completo

---

## 2. 📄 通知書 (Notificación a Cliente)

### Información Técnica
```yaml
Nombre: 労働者派遣法第35条の通知書
Área de impresión: H1:P66 (9 columnas x 66 filas)
Orientación: Portrait (vertical)
Tamaño papel: A4 (9)
Escala: 70% (¡IMPORTANTE! Reducido para caber en A4)
Estado actual: ⏳ POR IMPLEMENTAR
```

### Estructura del Documento

#### **Encabezado**
```
[Centrado] 労働者派遣法第35条の通知書
[Fecha de notificación]
```

#### **Destinatario**
```
御中
加藤木材工業株式会社
工場名: 本社工場
組織単位: 生産1部 2課
```

#### **Remitente**
```
ユニバーサル企画株式会社
派遣元責任者: [名前]
```

#### **Contenido**
```
下記の通り労働者を派遣しますので通知します。

1. 派遣期間: [開始日] ～ [終了日]
2. 派遣労働者: [氏名リスト]
3. 業務内容: [...]
4. 就業時間: [...]
5. 派遣料金: [...]
```

### Datos Dinámicos
- Todos los datos del contrato個別契約書
- Lista de empleados asignados (employee names)
- Fechas, horarios, tarifas

### Estado: ⏳ POR IMPLEMENTAR
**Prioridad: ALTA** (documento requerido legalmente)

**Plan de implementación:**
1. Crear template DOCX: `backend/templates/tsuchisho_template.docx`
2. Crear service: `backend/app/services/tsuchisho_service.py`
3. Añadir endpoint: `POST /kobetsu/{id}/generate-tsuchisho`

---

## 3. 📄 DAICHO (Registro Individual)

### Información Técnica
```yaml
Nombre: 派遣労働者 個人別台帳
Área de impresión: A1:BE78 (57 columnas x 78 filas - ¡MUY AMPLIO!)
Orientación: Portrait (vertical)
Tamaño papel: A4 (9)
Escala: Auto-fit (ajuste automático para caber en A4)
Estado actual: ⏳ POR IMPLEMENTAR
```

### Estructura del Documento

#### **Encabezado**
```
派遣労働者 個人別台帳
```

#### **Información Personal del Empleado**
```
氏名: [...]
生年月日: [...]
性別: [...]
国籍: [...]
住所: [...]
電話番号: [...]
```

#### **Información del Contrato**
```
派遣先: [...]
派遣期間: [...]
業務内容: [...]
就業時間: [...]
時給: [...]
```

#### **Historial de派遣**
Tabla con múltiples派遣 del mismo empleado.

### Datos Dinámicos
- Toda la información del employee
- Historial de contratos (kobetsu_keiyakusho) del empleado
- Datos de派遣先 para cada contrato

### Estado: ⏳ POR IMPLEMENTAR
**Prioridad: ALTA** (registro obligatorio)

**Plan de implementación:**
1. Crear template DOCX con tabla dinámica
2. Crear service: `backend/app/services/daicho_service.py`
3. Endpoint: `GET /employees/{id}/generate-daicho`

---

## 4-8. 📄 Otros Documentos (Prioridad Media/Baja)

### 4. 派遣元管理台帳
```yaml
Área: A1:AB71 (28 columnas x 71 filas)
Orientación: Portrait
Escala: 94%
Prioridad: 🔄 MEDIA
```
Registro de gestión para派遣元 (UNS企画).

### 5. 就業条件明示書
```yaml
Área: A1:AA56 (27 columnas x 56 filas)
Orientación: Portrait
Escala: 95%
Prioridad: 🔄 MEDIA
```
Documento de condiciones de empleo.

### 6. 就業状況報告書（本社)
```yaml
Área: A1:AI35 (35 columnas x 35 filas)
Orientación: Landscape (horizontal)
Prioridad: ⏳ BAJA
```
Reporte de estado laboral.

### 7. 契約書
```yaml
Área: A1:R54 (18 columnas x 54 filas)
Orientación: Landscape
Escala: 70%
Prioridad: ⏳ BAJA
```
Contrato de empleo del trabajador.

### 8. 雇入れ時の待遇情報
```yaml
Área: Toda la hoja (W48)
Orientación: Portrait
Prioridad: ⏳ BAJA
```
Información de tratamiento al momento de contratación.

---

## 🎯 Plan de Implementación Recomendado

### Fase 1: Validar個別契約書X (Sprint Actual)
- [x] Template DOCX creado
- [x] Service implementado
- [ ] **VALIDAR** que el formato coincida 100% con Excel
- [ ] **AÑADIR** tabla de tarifas calculada
- [ ] **TEST** con datos reales

### Fase 2: Implementar通知書 y DAICHO (Sprint 2 - Próximas 2 semanas)
- [ ] Crear template通知書
- [ ] Crear service通知書
- [ ] Crear template DAICHO
- [ ] Crear service DAICHO
- [ ] Tests unitarios

### Fase 3: Documentos Restantes (Sprint 3-4 - 1 mes)
- [ ] 派遣元管理台帳
- [ ] 就業条件明示書
- [ ] Otros 3 documentos

---

## 🔧 Herramientas para Generar PDFs

### Opción 1: python-docx + python-docx2pdf ✅ ACTUAL
```python
from docx import Document
from docx2pdf import convert

doc = Document('template.docx')
# Rellenar campos
doc.save('output.docx')
convert('output.docx', 'output.pdf')
```

**Pros:**
- ✅ Control total del layout
- ✅ Fácil mantenimiento
- ✅ Soporta tablas complejas

**Cons:**
- ⚠️ Requiere calibración precisa para coincidir con Excel

### Opción 2: ReportLab (PDF directo)
```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

c = canvas.Canvas("output.pdf", pagesize=A4)
c.drawString(100, 750, "人材派遣個別契約書")
c.save()
```

**Pros:**
- ✅ Control pixel-perfect
- ✅ No necesita conversión DOCX→PDF

**Cons:**
- ⚠️ Más difícil de mantener
- ⚠️ Código más complejo

### Opción 3: Jinja2 HTML + WeasyPrint
```python
from jinja2 import Template
from weasyprint import HTML

template = Template('<html>...</html>')
html = template.render(data)
HTML(string=html).write_pdf('output.pdf')
```

**Pros:**
- ✅ Templates HTML familiares
- ✅ CSS para styling

**Cons:**
- ⚠️ Dificultad para layouts complejos tipo Excel

---

## 📝 Próximos Pasos

1. **VALIDAR個別契約書 actual:**
   - Imprimir desde Excel
   - Generar PDF desde web
   - Comparar lado a lado
   - Ajustar diferencias

2. **Extraer templates de Excel:**
   - Copiar formato exacto de通知書
   - Copiar formato exacto de DAICHO
   - Crear DOCX templates

3. **Implementar services:**
   - Seguir estructura de `kobetsu_pdf_service.py`
   - Reutilizar lógica de datos
   - Tests unitarios

4. **UI para generar documentos:**
   - Botones en UI para cada documento
   - Preview antes de generar
   - Descarga múltiple

---

## 📞 Notas Importantes

1. **Escalas en Excel:**
   - 個別契約書X: 96% → Casi tamaño completo
   - 通知書: 70% → Muy reducido (letter pequeña)
   - 契約書: 70% → Muy reducido
   - Importante replicar estas escalas para match visual

2. **Áreas de impresión específicas:**
   - Excel tiene rangos exactos configurados
   - En PDF, debemos respetar estos límites
   - No imprimir fuera del área configurada

3. **Datos dinámicos vs estáticos:**
   - Separar claramente qué es variable
   - Mantener texto legal estático en templates
   - Facilitar actualizaciones futuras

---

**Documento generado para:** UNS Kobetsu Keiyakusho
**Propósito:** Guiar implementación de templates de documentos
**Autor:** Claude Code Analysis
**Fecha:** 2025-11-26
