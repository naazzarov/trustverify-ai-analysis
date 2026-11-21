import argparse
import posixpath
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET

CORE = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
PRESENTATION = "http://schemas.openxmlformats.org/presentationml/2006/main"
DRAWING = "http://schemas.openxmlformats.org/drawingml/2006/main"
OFFICE_RELS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
COVER = "ppt/slides/slide1.xml"
AUTHOR = "BAHODIR KODIRJON UGLI NAZAROV"

for prefix, namespace in [("cp", CORE), ("dc", DC), ("p", PRESENTATION), ("a", DRAWING), ("r", OFFICE_RELS)]:
    ET.register_namespace(prefix, namespace)


def core_properties(data):
    tree = ET.fromstring(data)
    fields = [
        (DC, "creator", AUTHOR),
        (CORE, "lastModifiedBy", AUTHOR),
        (DC, "title", "TrustVerify: Executable Verification of AI-Generated Data Analysis"),
    ]
    for namespace, tag, value in fields:
        qualified = f"{{{namespace}}}{tag}"
        element = tree.find(qualified)
        if element is None:
            element = ET.SubElement(tree, qualified)
        element.text = value
    return ET.tostring(tree, encoding="utf-8", xml_declaration=True)


def cover_duotone(source, logo, ink, background):
    rels = ET.fromstring(source.read("ppt/slides/_rels/slide1.xml.rels"))
    matching_ids = set()
    for rel in rels:
        if rel.attrib["Type"].endswith("/image"):
            target = rel.attrib["Target"]
            name = target.lstrip("/") if target.startswith("/") else posixpath.normpath(
                posixpath.join(posixpath.dirname(COVER), target)
            )
            if source.read(name) == logo:
                matching_ids.add(rel.attrib["Id"])

    tree = ET.fromstring(source.read(COVER))
    pictures = tree.findall(f".//{{{PRESENTATION}}}pic/{{{PRESENTATION}}}blipFill/{{{DRAWING}}}blip")
    matches = [picture for picture in pictures if picture.get(f"{{{OFFICE_RELS}}}embed") in matching_ids]
    if len(matches) != 1:
        raise ValueError(f"Expected one cover wordmark, found {len(matches)}")

    # Map the original black strokes and white field to ink and the cover background.
    effect = ET.Element(f"{{{DRAWING}}}duotone")
    ET.SubElement(effect, f"{{{DRAWING}}}srgbClr", val=ink)
    ET.SubElement(effect, f"{{{DRAWING}}}srgbClr", val=background)
    matches[0].insert(0, effect)
    return ET.tostring(tree, encoding="utf-8", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("presentation", type=Path)
    parser.add_argument("wordmark", type=Path)
    parser.add_argument("ink")
    parser.add_argument("background")
    args = parser.parse_args()
    temporary = args.presentation.with_suffix(".styled.pptx")
    with ZipFile(args.presentation) as source, ZipFile(temporary, "w", ZIP_DEFLATED) as destination:
        for name in source.namelist():
            if name == "docProps/core.xml":
                data = core_properties(source.read(name))
            elif name == COVER:
                data = cover_duotone(source, args.wordmark.read_bytes(), args.ink, args.background)
            else:
                data = source.read(name)
            destination.writestr(name, data)
    temporary.replace(args.presentation)


if __name__ == "__main__":
    main()
