database(
    thermoLibraries = ['KlippensteinH2O2','primaryThermoLibrary','CBS_QB3_1dHR', 'DFT_QCI_thermo', 'GRI-Mech3.0']
)

species(
    label='Cineole',
    structure=SMILES("C12(CCC(C(C)(C)O2)CC1)C"),
)

species(
    label='R1',
    structure=SMILES("[CH2]C12CCC(CC1)C(C)(C)O2"),
)

species(
    label='R1a',
    structure=SMILES("C=C1CCC(CC1)C(C)(C)[O]"),
)

species(
    label='R1b',
    structure=SMILES("[CH2]CC1CCC(=C)OC1(C)C"),
)

species(
    label='R1OO',
    structure=SMILES("CC1(C)OC2(CCC1CC2)CO[O]"),
)

species(
    label='R2',
    structure=SMILES("CC12C[CH]C(CC1)C(C)(C)O2"),
)

species(
    label='R2a',
    structure=SMILES("C=CC1CC[C](C)OC1(C)C"),
)

species(
    label='R2b',
    structure=SMILES("[CH2]CC1(C)CC=CC(C)(C)O1"),
)

species(
    label='R2c',
    structure=SMILES("C[C](C)OC1(C)CC=CCC1"),
)

species(
    label='R2OO',
    structure=SMILES("CC12CCC(C(C1)O[O])C(C)(C)O2"),
)

species(
    label='R3',
    structure=SMILES("[CH2]C1(C)OC2(C)CCC1CC2"),
)

species(
    label='R3a',
    structure=SMILES("C=C(C)C1CCC(C)([O])CC1"),
)

species(
    label='R3b',
    structure=SMILES("C=C(C)OC1(C)CC[CH]CC1"),
)

species(
    label='R3OO',
    structure=SMILES("CC12CCC(CC1)C(C)(CO[O])O2"),
)

species(
    label='R4',
    structure=SMILES("CC12[CH]CC(CC1)C(C)(C)O2"),
)

species(
    label='R4a',
    structure=SMILES("[CH2]CC1CC=C(C)OC1(C)C"),
)

species(
    label='R4b',
    structure=SMILES("CC1=CCC(CC1)C(C)(C)[O]"),
)

species(
    label='R4OO',
    structure=SMILES("CC1(C)OC2(C)CCC1CC2O[O]"),
)

species(
    label='R5',
    structure=SMILES("CC12CC[C](CC1)C(C)(C)O2"),
)

species(
    label='R5a',
    structure=SMILES("CC(C)=C1CCC(C)([O])CC1"),
)

species(
    label='R5OO',
    structure=SMILES("CC12CCC(CC1)(O[O])C(C)(C)O2"),
)

quantumMechanics(
    software='mopac',
    method='pm6-d3', # pm3 vs. pm6 vs. pm7 ?   ->   the higher the newer
    fileStore='QMfiles', # relative to where you run it? defaults to inside the output folder.
    scratchDirectory = None, # not currently used
    onlyCyclics = True,
    maxRadicalNumber = 0,
)