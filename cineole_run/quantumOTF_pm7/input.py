database(
    thermoLibraries = ['KlippensteinH2O2','primaryThermoLibrary','CBS_QB3_1dHR', 'DFT_QCI_thermo', 'GRI-Mech3.0','Cineole'],
    reactionLibraries = [('Cineole',False)],
    seedMechanisms = ['KlippensteinH2O2'],
    kineticsDepositories = ['training'],
    kineticsFamilies = 'default',
    kineticsEstimator = 'rate rules',
)

generatedSpeciesConstraints(
    allowed = [],
    maximumCarbonAtoms = 10,
    maximumOxygenAtoms = 5,
    maximumRadicalElectrons = 2,
    allowSingletO2 = False,
)

species(
    label='Cineole',
    reactive=True,
    structure=SMILES("C12(CCC(C(C)(C)O2)CC1)C"),
)

species(
    label='O2',
    reactive=True,
    structure=SMILES("[O][O]"),
)

species(
    label='Cl',
    reactive=False,
    structure=SMILES("[Cl]"),
)

species(
    label='HCl',
    reactive=False,
    structure=SMILES("Cl"),
)


species(
    label='He',
    reactive=False,
    structure=SMILES("[He]"),
)

species(
    label='Cl2',
    reactive=False,
    structure=SMILES("ClCl"),
)

simpleReactor(
    temperature=(550,'K'),
    pressure=(4,'torr'),
    initialMoleFractions={
        "Cineole": 3.7e-4,
        "Cl2": 8.4e-4,
        "Cl": 2.565e-5,
        "O2": 2.56e-1,
        "He": 7.42e-1,
    },
    terminationTime=(1e-3,'s'),
)

simpleReactor(
    temperature=(650,'K'),
    pressure=(4,'torr'),
    initialMoleFractions={
        "Cineole": 3.7e-4,
        "Cl2": 8.41e-4,
        "Cl": 2.52e-5,
        "O2": 2.52e-1,
        "He": 7.46e-1,
    },
    terminationTime=(1e-3,'s'),
)


simulator(
    atol=1e-16,
    rtol=1e-8,
)

model(
    toleranceKeepInEdge=0.0,
    toleranceMoveToCore=0.01,
    toleranceInterruptSimulation=0.01,
    maximumEdgeSpecies=1000000
)

quantumMechanics(
    software='mopac',
    method='pm7', # pm3 vs. pm6 vs. pm7 ?   ->   the higher the newer
    fileStore='QMfiles', # relative to where you run it? defaults to inside the output folder.
    scratchDirectory = None, # not currently used
    onlyCyclics = True,
    maxRadicalNumber = 0,
)


options(
    units='si',
    saveRestartPeriod=(2,'hour'),
    generateOutputHTML=False,
    generatePlots=False,
)