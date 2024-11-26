import xml.etree.ElementTree as ET

if __name__ == "__main__":
    # load ggb file by pid
    # pid = int(input("Input ggb pid:"))
    pid = 1

    # get root of XML tree
    ggb_tree = ET.parse(f"ggb_unzip/{pid}_unzip/geogebra.xml")
    root = ggb_tree.getroot()
    # get sub-elements of root
    # for child in root:
    #     print(child.tag, child.attrib)

    # show euclidian view
    euclidianview = root.find("euclidianView")
    coordsystem = euclidianview.find("coordSystem")
    center_x = coordsystem.get("xZero")
    center_y = coordsystem.get("yZero")
    print(f"coord system center: (x={center_x}, y={center_y})")

    # get construction
    construction = root.find("construction")

    # get elements in construction
    for element in construction:
        # get point in elements
        if element.attrib.get("type") == "point":
            point_label = element.attrib.get("label")
            point_x = element.find("coords").get("x")
            point_y = element.find("coords").get("y")
            point_z = element.find("coords").get("z")
            print(f"point {point_label}: (x={point_x}, y={point_y}, z={point_z})")
