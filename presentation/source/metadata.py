from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import sys
import xml.etree.ElementTree as ET
p=Path(sys.argv[1]);tmp=p.with_suffix('.metadata.pptx')
ns={'cp':'http://schemas.openxmlformats.org/package/2006/metadata/core-properties','dc':'http://purl.org/dc/elements/1.1/'}
with ZipFile(p) as src, ZipFile(tmp,'w',ZIP_DEFLATED) as dst:
    for item in src.infolist():
        data=src.read(item.filename)
        if item.filename=='docProps/core.xml':
            tree=ET.fromstring(data)
            for tag,val in [('dc:creator','BAHODIR KODIRJON UGLI NAZAROV'),('cp:lastModifiedBy','BAHODIR KODIRJON UGLI NAZAROV'),('dc:title','TrustVerify: Executable Verification of AI-Generated Data Analysis')]:
                q='{'+ns[tag.split(':')[0]]+'}'+tag.split(':')[1]
                e=tree.find(q)
                if e is None:e=ET.SubElement(tree,q)
                e.text=val
            data=ET.tostring(tree,encoding='utf-8',xml_declaration=True)
        dst.writestr(item,data)
tmp.replace(p)
