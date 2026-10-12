import zipfile
from pathlib import Path
from foodbank.ingest import sheet_rows


def test_streaming_reads_sparse_shared_inline_and_cached_cells(tmp_path):
    path=tmp_path/'small.xlsx'
    main='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    office='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{main}" xmlns:r="{office}"><sheets><sheet name="Example" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/sharedStrings.xml',f'<sst xmlns="{main}"><si><t>HEADERID</t></si><si><r><t>001</t></r><r><t>23</t></r></si></sst>')
        z.writestr('xl/worksheets/sheet1.xml',f'<worksheet xmlns="{main}"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="C1" t="inlineStr"><is><t>quantity</t></is></c></row><row r="2"><c r="A2" t="s"><v>1</v></c><c r="C2"><f>1+1</f><v>2</v></c></row></sheetData></worksheet>')
    with zipfile.ZipFile(path) as z:
        rows=list(sheet_rows(z,'Example'))
    assert rows==[{'A':'HEADERID','C':'quantity'},{'A':'00123','C':'2'}]
