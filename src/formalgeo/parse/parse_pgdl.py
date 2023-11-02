from formalgeo.parse.basic import parse_geo_predicate, parse_equal_predicate


def parse_predicate_gdl(predicate_GDL):
    """parse predicate_GDL to logic form."""
    parsed_GDL = {  # preset Construction
        "Preset": predicate_GDL["Preset"],
        "Entity": {},
        "Relation": {},
        "Attribution": {}
    }
    entities = predicate_GDL["Entity"]  # parse entity
    for item in entities:
        name, para, para_len = parse_geo_predicate(item, True)
        parsed_GDL["Entity"][name] = {
            "vars": tuple(para),
            "para_len": tuple(para_len),
            "ee_check": tuple(parse_ee_check(entities[item]["ee_check"])),
            "multi": tuple(parse_multi(entities[item]["multi"])),
            "extend": tuple(parse_extend(entities[item]["extend"]))
        }

    relations = predicate_GDL["Relation"]  # parse relation
    for item in relations:
        name, para, para_len = parse_geo_predicate(item, True)
        if "fv_check" in relations[item]:
            parsed_GDL["Relation"][name] = {
                "vars": tuple(para),
                "para_len": tuple(para_len),
                "ee_check": tuple(parse_ee_check(relations[item]["ee_check"])),
                "fv_check": tuple(parse_fv_check(relations[item]["fv_check"])),
                "multi": tuple(parse_multi(relations[item]["multi"])),
                "extend": tuple(parse_extend(relations[item]["extend"]))
            }
        else:
            parsed_GDL["Relation"][name] = {
                "vars": tuple(para),
                "para_len": tuple(para_len),
                "ee_check": tuple(parse_ee_check(relations[item]["ee_check"])),
                "multi": tuple(parse_multi(relations[item]["multi"])),
                "extend": tuple(parse_extend(relations[item]["extend"]))
            }

    attributions = predicate_GDL["Attribution"]  # parse attribution
    for item in attributions:
        name, para, para_len = parse_geo_predicate(item, True)
        if "fv_check" in attributions[item]:
            parsed_GDL["Attribution"][name] = {
                "vars": tuple(para),
                "para_len": tuple(para_len),
                "ee_check": tuple(parse_ee_check(attributions[item]["ee_check"])),
                "fv_check": tuple(parse_fv_check(attributions[item]["fv_check"])),
                "sym": attributions[item]["sym"],
                "multi": tuple(parse_multi(attributions[item]["multi"]))
            }
        else:
            parsed_GDL["Attribution"][name] = {
                "vars": tuple(para),
                "para_len": tuple(para_len),
                "ee_check": tuple(parse_ee_check(attributions[item]["ee_check"])),
                "sym": attributions[item]["sym"],
                "multi": tuple(parse_multi(attributions[item]["multi"]))
            }

    return parsed_GDL


def parse_ee_check(ee_check):
    """
    parse ee_check to logic form.
    >> parse_ee_check(['Triangle(ABC)'])
    [('Triangle', ('a', 'b', 'c'))]
    >> parse_ee_check(['Line(AO)', 'Line(CO)'])
    [('Line', ('a', 'o')), ('Line', ('c', 'o'))]
    """
    results = []
    for item in ee_check:
        name, item_para, _ = parse_geo_predicate(item, True)
        results.append((name, tuple(item_para)))
    return results


def parse_fv_check(fv_check):
    """
    parse fv_check to logic form.
    >> parse_fv_check(['O,AB,CD'])
    ['01234']
    >> parse_fv_check(['AD,ABC', 'AB,ABC', 'AC,ABC'])
    ['01023', '01012', '01021']
    """
    results = []
    for item in fv_check:
        checked = []
        result = []
        for i in item.replace(",", ""):
            if i not in checked:
                checked.append(i)
            result.append(str(checked.index(i)))
        results.append("".join(result))
    return results


def parse_multi(multi):
    """
    parse multi to logic form.
    >> _parse_multi(['BCA', 'CAB'])
    [('b', 'c', 'a'), ('c', 'a', 'b')]
    >> _parse_multi(['M,BA'])
    [('m', 'b', 'a')]
    """
    return [tuple(parsed_multi.replace(",", "").lower()) for parsed_multi in multi]


def parse_extend(extend):
    """
    parse extend to logic form.
    >> parse_extend(['Equal(MeasureOfAngle(AOC),90)'])
    [('Equal', (('MeasureOfAngle', ('a', 'o', 'c')), '90'))]
    >> parse_extend(['Perpendicular(AB,CB)', 'IsAltitude(AB,ABC)'])
    [('Perpendicular', ('a', 'b', 'c', 'b')), ('IsAltitude', ('a', 'b', 'a', 'b', 'c'))]
    """
    results = []
    for extend_item in extend:
        if extend_item.startswith("Equal"):
            parsed_equal, _ = parse_equal_predicate(extend_item, True)
            results.append(parsed_equal)
        else:
            extend_name, extend_para, _ = parse_geo_predicate(extend_item, True)
            results.append((extend_name, tuple(extend_para)))
    return results
