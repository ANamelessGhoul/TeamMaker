
specNames = ['Game Design', 'Programming','2D Art', '3D Art', 'Narrative Design', 'Music', 'Sound']
roleNames = ['Game Designer', 'Programmer','2D Artist', '3D Artist', 'Narrative Designer', 'Musician', 'Sound Designer']

def getSpecializations():
    return specNames[:]

def getRoles():
    return roleNames[:]

def decodeSpecs(specs):
    decoded = []
    for i in range(len(specNames)):
        if specsContains(specs, i):
            decoded.append(specNames[i])
    return decoded

def specsContains (specs, spec):
    return (specs & (1 << spec)) != 0