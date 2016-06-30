#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from unittest import TestCase, TestLoader, TextTestRunner
from external.wip import work_in_progress

from rmgpy import settings
from rmgpy.molecule import Molecule
from rmgpy.rmg.main import Species
from rmgpy.data.solvation import DatabaseError, SoluteData, SolvationDatabase, SolventLibrary, SolventData
from rmgpy.rmg.main import RMG
from rmgpy.thermo.wilhoit import Wilhoit
from rmgpy.thermo import ThermoData

###################################################

class TestSoluteDatabase(TestCase):
    
    def setUp(self):
        self.database = SolvationDatabase()
        self.database.load(os.path.join(settings['database.directory'], 'solvation'))
    
    def runTest(self):
        pass
    
    def testSoluteLibrary(self):
        "Test we can obtain solute parameters from a library"
        species = Species(molecule=[Molecule(SMILES='COC=O')]) #methyl formate - we know this is in the solute library
        
        libraryData = self.database.getSoluteDataFromLibrary(species, self.database.libraries['solute'])
        self.assertEqual(len(libraryData), 3)
        
        soluteData = self.database.getSoluteData(species)
        self.assertTrue(isinstance(soluteData, SoluteData))
        
        S = soluteData.S
        self.assertEqual(S, 0.68)
        self.assertTrue(soluteData.V is not None)
     
    def testMcGowan(self):
        "Test we can calculate and set the McGowan volume for species containing H,C,O,N or S"
        self.testCases = [
                          ['CCCCCCCC', 1.2358], #n-octane, in library
                          ['C(CO)O', 0.5078], #ethylene glycol
                          ['CC#N', 0.4042], #acetonitrile
                          ['CCS', 0.5539] #ethanethiol
                           ]
        
        for smiles, volume in self.testCases:
            species = Species(molecule=[Molecule(SMILES=smiles)])
            soluteData = self.database.getSoluteData(species)
            soluteData.setMcGowanVolume(species) # even if it was found in library, recalculate
            self.assertTrue(soluteData.V is not None) # so if it wasn't found in library, we should have calculated it
            self.assertAlmostEqual(soluteData.V, volume) # the volume is what we expect given the atoms and bonds 
            
    
    def testDiffusivity(self):
        "Test that for a given solvent viscosity and temperature we can calculate a solute's diffusivity"
        species = Species(molecule=[Molecule(SMILES='O')])  # water
        soluteData = self.database.getSoluteData(species)
        T = 298.
        solventViscosity = 0.00089  # water is about 8.9e-4 Pa.s
        D = soluteData.getStokesDiffusivity(T, solventViscosity)  # m2/s
        self.assertAlmostEqual((D * 1e9), 1.3, 1)
        # self-diffusivity of water is about 2e-9 m2/s
        
    def testSolventLibrary(self):
        "Test we can obtain solvent parameters from a library"
        solventData = self.database.getSolventData('water')
        self.assertTrue(solventData is not None)
        self.assertEqual(solventData.s_h, 2.836)
        self.assertRaises(DatabaseError, self.database.getSolventData, 'orange_juice')
        
    def testViscosity(self):
        "Test we can calculate the solvent viscosity given a temperature and its A-E correlation parameters"
        solventData = self.database.getSolventData('water')  
        self.assertAlmostEqual(solventData.getSolventViscosity(298), 0.0009155)

    def testSoluteGeneration(self):
        "Test we can estimate Abraham solute parameters correctly using group contributions"
        
        self.testCases = [
        ['1,2-ethanediol', 'C(CO)O', 0.823, 0.685, 0.327, 2.572, 0.693, None],
        ]
        
        for name, smiles, S, B, E, L, A, V in self.testCases:
            species = Species(molecule=[Molecule(SMILES=smiles)])
            soluteData = self.database.getSoluteDataFromGroups(Species(molecule=[species.molecule[0]]))
            self.assertAlmostEqual(soluteData.S, S, places=2)
            self.assertAlmostEqual(soluteData.B, B, places=2)
            self.assertAlmostEqual(soluteData.E, E, places=2)
            self.assertAlmostEqual(soluteData.L, L, places=2)
            self.assertAlmostEqual(soluteData.A, A, places=2)

    def testLonePairSoluteGeneration(self):
        "Test we can obtain solute parameters via group additivity for a molecule with lone pairs"
        molecule=Molecule().fromAdjacencyList(
"""
CH2_singlet
multiplicity 1
1 C u0 p1 c0 {2,S} {3,S}
2 H u0 p0 c0 {1,S}
3 H u0 p0 c0 {1,S}
""")
        species = Species(molecule=[molecule])
        soluteData = self.database.getSoluteDataFromGroups(species)
        self.assertTrue(soluteData is not None)
        
    def testSoluteDataGenerationAmmonia(self):
        "Test we can obtain solute parameters via group additivity for ammonia"
        molecule=Molecule().fromAdjacencyList(
"""
1 N u0 p1 c0 {2,S} {3,S} {4,S}
2 H u0 p0 c0 {1,S}
3 H u0 p0 c0 {1,S}
4 H u0 p0 c0 {1,S}
""")
        species = Species(molecule=[molecule])
        soluteData = self.database.getSoluteDataFromGroups(species)
        self.assertTrue(soluteData is not None)
        
    def testSoluteDataGenerationAmide(self):
        "Test that we can obtain solute parameters via group additivity for an amide"        
        molecule=Molecule().fromAdjacencyList(
"""
1  N u0 p1 {2,S} {3,S} {4,S}
2   H   u0 {1,S}
3   C u0 {1,S} {6,S} {7,S} {8,S}
4   C  u0 {1,S} {5,D} {9,S}
5   O  u0 p2 {4,D}
6   H   u0 {3,S}
7   H   u0 {3,S}
8   H   u0 {3,S}
9   H   u0 {4,S}
""")
        species = Species(molecule=[molecule])
        soluteData = self.database.getSoluteDataFromGroups(species)
        self.assertTrue(soluteData is not None)

    def testSoluteDataGenerationCO(self):
        "Test that we can obtain solute parameters via group additivity for CO."        
        molecule=Molecule().fromAdjacencyList(
"""
1  C u0 p1 c-1 {2,T}
2  O u0 p1 c+1 {1,T}
""")
        species = Species(molecule=[molecule])
        soluteData = self.database.getSoluteDataFromGroups(species)
        self.assertTrue(soluteData is not None)
    
    def testRadicalandLonePairGeneration(self):
        """
        Test we can obtain solute parameters via group additivity for a molecule with both lone 
        pairs and a radical
        """
        molecule=Molecule().fromAdjacencyList(
"""
[C]OH
multiplicity 2
1 C u1 p1 c0 {2,S}
2 O u0 p2 c0 {1,S} {3,S}
3 H u0 p0 c0 {2,S}
""")
        species = Species(molecule=[molecule])
        soluteData = self.database.getSoluteDataFromGroups(species)
        self.assertTrue(soluteData is not None)

    def testCorrectionGeneration(self):
        "Test we can estimate solvation thermochemistry."
        self.testCases = [
        # solventName, soluteName, soluteSMILES, Hsolv, Gsolv
        ['water', 'acetic acid', 'C(C)(=O)O', -56500, -6700*4.184],
        ['water', 'naphthalene', 'C1=CC=CC2=CC=CC=C12', -42800, -2390*4.184],
        ['1-octanol', 'octane', 'CCCCCCCC', -40080, -4180*4.184],
        ['1-octanol', 'tetrahydrofuran', 'C1CCOC1', -28320, -3930*4.184],
        ['benzene', 'toluene', 'C1(=CC=CC=C1)C', -37660, -5320*4.184],
        ['benzene', '1,4-dioxane', 'C1COCCO1', -39030, -5210*4.184]
        ]
        
        for solventName, soluteName, smiles, H, G in self.testCases:
            species = Species(molecule=[Molecule(SMILES=smiles)])
            soluteData = self.database.getSoluteData(species)
            solventData = self.database.getSolventData(solventName)
            solvationCorrection = self.database.getSolvationCorrection(soluteData, solventData)
            self.assertAlmostEqual(solvationCorrection.enthalpy / 10000., H / 10000., 0, msg="Solvation enthalpy discrepancy ({2:.0f}!={3:.0f}) for {0} in {1}".format(soluteName, solventName, solvationCorrection.enthalpy, H))  #0 decimal place, in 10kJ.
            self.assertAlmostEqual(solvationCorrection.gibbs / 10000., G / 10000., 0, msg="Solvation Gibbs free energy discrepancy ({2:.0f}!={3:.0f}) for {0} in {1}".format(soluteName, solventName, solvationCorrection.gibbs, G))

    def testInitialSpecies(self):
        " Test we can check whether the solvent is listed as one of the initial species in various scenarios "

        # Case 1. when SMILES for solvent is available, the molecular structures of the initial species and the solvent
        # are compared to check whether the solvent is in the initial species list

        # Case 1-1: the solvent water is not in the initialSpecies list, so it raises Exception
        rmg=RMG()
        rmg.initialSpecies = []
        solute = Species(label='n-octane', molecule=[Molecule().fromSMILES('C(CCCCC)CC')])
        rmg.initialSpecies.append(solute)
        rmg.solvent = 'water'
        solventStructure = Species().fromSMILES('O')
        self.assertRaises(Exception, self.database.checkSolventinInitialSpecies, rmg, solventStructure)

        # Case 1-2: the solvent is now octane and it is listed as the initialSpecies. Although the string
        # names of the solute and the solvent are different, because the solvent SMILES is provided,
        # it can identify the 'n-octane' as the solvent
        rmg.solvent = 'octane'
        solventStructure = Species().fromSMILES('CCCCCCCC')
        self.database.checkSolventinInitialSpecies(rmg, solventStructure)
        self.assertTrue(rmg.initialSpecies[0].isSolvent)

        # Case 2: the solvent SMILES is not provided. In this case, it can identify the species as the
        # solvent by looking at the string name.

        # Case 2-1: Since 'n-octane and 'octane' are not equal, it raises Exception
        solventStructure = None
        self.assertRaises(Exception, self.database.checkSolventinInitialSpecies, rmg, solventStructure)

        # Case 2-2: The label 'n-ocatne' is corrected to 'octane', so it is identified as the solvent
        rmg.initialSpecies[0].label = 'octane'
        self.database.checkSolventinInitialSpecies(rmg, solventStructure)
        self.assertTrue(rmg.initialSpecies[0].isSolvent)

    def testSolventMolecule(self):
        " Test we can give a proper value for the solvent molecular structure when different solvent databases are given "

        # solventlibrary.entries['solvent_label'].item should be the instance of Species with the solvent's molecular structure
        # if the solvent database contains the solvent SMILES or adjacency list. If not, then item is None

        # Case 1: When the solventDatabase does not contain the solvent SMILES, the item attribute is None
        solventlibrary = SolventLibrary()
        solventlibrary.loadEntry(index=1, label='water', solvent=None)
        self.assertTrue(solventlibrary.entries['water'].item is None)

        # Case 2: When the solventDatabase contains the correct solvent SMILES, the item attribute is the instance of
        # Species with the correct solvent molecular structure
        solventlibrary.loadEntry(index=2, label='octane', solvent=None, molecule='CCCCCCCC')
        solventSpecies = Species().fromSMILES('C(CCCCC)CC')
        self.assertTrue(solventSpecies.isIsomorphic(solventlibrary.entries['octane'].item))

        # Case 3: When the solventDatabase contains the correct solvent adjacency list, the item attribute is the instance of
        # the species with the correct solvent molecular structure.
        # This will display the SMILES Parse Error message from the external function, but ignore it.
        solventlibrary.loadEntry(index=3, label='ethanol', solvent=None, molecule=
"""
1 C u0 p0 c0 {2,S} {4,S} {5,S} {6,S}
2 C u0 p0 c0 {1,S} {3,S} {7,S} {8,S}
3 O u0 p2 c0 {2,S} {9,S}
4 H u0 p0 c0 {1,S}
5 H u0 p0 c0 {1,S}
6 H u0 p0 c0 {1,S}
7 H u0 p0 c0 {2,S}
8 H u0 p0 c0 {2,S}
9 H u0 p0 c0 {3,S}
""")
        solventSpecies = Species().fromSMILES('CCO')
        self.assertTrue(solventSpecies.isIsomorphic(solventlibrary.entries['ethanol'].item))

        # Case 4: when the solventDatabase contains incorrect values for the molecule attribute, it raises Exception
        # This will display the SMILES Parse Error message from the external function, but ignore it.
        self.assertRaises(Exception, solventlibrary.loadEntry, index=4, label='benzene', solvent=None, molecule='ring')

    def testSolventCoolPropInfo(self):
        " Test we can give proper values for CoolProp related Species attributes when different solvet database are given"

        # Case 1: When the solventDatabase does not contain any CoolProp related info, inCoolProp and
        # NameinCoolProp attributes are all None
        solventlibrary = SolventLibrary()
        solventdata = SolventData()
        solventlibrary.loadEntry(index=1, label='water', solvent=solventdata)
        self.assertTrue(solventlibrary.entries['water'].data.inCoolProp is None)
        self.assertTrue(solventlibrary.entries['water'].data.NameinCoolProp is None)

        # Case 2: When the solventDatabase does contain CoolProp related info and the solvent is available in CoolProp,
        # 'inCoolProp' returns True and 'NameinCoolProp' returns the solvent's name recognizable by CoolProp
        solventdata.inCoolProp = True
        solventdata.NameinCoolProp = 'CycloHexane'
        solventlibrary.loadEntry(index=2, label='cyclohexane', solvent=solventdata)
        self.assertTrue(solventlibrary.entries['cyclohexane'].data.inCoolProp)
        self.assertTrue(solventlibrary.entries['cyclohexane'].data.NameinCoolProp is 'CycloHexane')

        # Case 3: When the solventDatabase does contain CoolProp related info and the solvent is unavailable in CoolProp,
        # 'inCoolProp' returns True and 'NameinCoolProp' returns None
        solventdata.inCoolProp = False
        solventdata.NameinCoolProp = None
        solventlibrary.loadEntry(index=3, label='hexadecane', solvent=solventdata)
        self.assertFalse(solventlibrary.entries['hexadecane'].data.inCoolProp)
        self.assertTrue(solventlibrary.entries['hexadecane'].data.NameinCoolProp is None)

    def testSolvent_H298_S98(self):
        " Test we can calculate the solvent's standard enthalpy of formation and standard entropy given the solvent's CoolProp name and gas Thermo"

        # generate the gas phase wilhoit for water
        thermoData = ThermoData(Tdata = ([300,400,500,600,800,1000,1500],'K'),
                                Cpdata = ([8.038,8.18,8.379,8.624,9.195,9.766,11.019],'cal/(mol*K)'),
                                H298 = (-57.797,'kcal/mol'), S298 = (45.084,'cal/(mol*K)'),)
        spc = Species().fromSMILES('O')
        Cp0 = spc.calculateCp0()
        CpInf = spc.calculateCpInf()
        Tdata = thermoData.Tdata.value_si
        Cpdata = thermoData._Cpdata.value_si
        H298 = thermoData._H298.value_si
        S298 = thermoData._S298.value_si
        wilhoit_gas = Wilhoit().fitToData(Tdata, Cpdata, Cp0, CpInf, H298, S298)

        solventNameinCoolProp = 'water'
        H298_liquid = self.database.calcSolventH298(solventNameinCoolProp, wilhoit_gas) # in J/mol
        self.assertAlmostEqual(H298_liquid / 1000., -285.8, 0) # -285.8 kJ/mol is the standard formation enthalpy of liquid water. Obtained from NIST

        S298_liquid = self.database.calcSolventS298(solventNameinCoolProp, wilhoit_gas) # in J/mol/K
        self.assertAlmostEqual(S298_liquid, 69.95, 0) # 69.95 J/mol/K is the standard entropy of liquid water. Obtained from NIST

    def testSolventThermo(self):
        " Test we can get the correct Wilhoit model for the solvent species"

        # generate the gas phase wilhoit for water
        thermoData = ThermoData(Tdata = ([300,400,500,600,800,1000,1500],'K'),
                                Cpdata = ([8.038,8.18,8.379,8.624,9.195,9.766,11.019],'cal/(mol*K)'),
                                H298 = (-57.797,'kcal/mol'), S298 = (45.084,'cal/(mol*K)'),)
        spc = Species().fromSMILES('O')
        spc.SolventNameinCoolProp = 'water'
        Cp0 = spc.calculateCp0()
        CpInf = spc.calculateCpInf()
        Tdata = thermoData.Tdata.value_si
        Cpdata = thermoData._Cpdata.value_si
        H298 = thermoData._H298.value_si
        S298 = thermoData._S298.value_si
        wilhoit_gas = Wilhoit().fitToData(Tdata, Cpdata, Cp0, CpInf, H298, S298)

        wilhoit_liquid = self.database.getSolventThermo(spc, wilhoit_gas)

        # validation data set. Obtained by adjusting the base enthalpy, entropy, and free energy of the CoolProp values
        T_val =  [300., 400., 500.] # K
        H_val = [-285.3, -277.8, -269.8] # kJ/mol
        S_val = [70.8, 92.6, 110.2] # J/mol/K
        G_val = [-306.6, -314.8, -324.9] # kJ/mol

        for i in range(len(T_val)):
            self.assertAlmostEqual(wilhoit_liquid.getEnthalpy(T_val[i]) / 1000., H_val[i], 0)
            self.assertAlmostEqual(wilhoit_liquid.getEntropy(T_val[i]), S_val[i], 0)
            self.assertAlmostEqual(wilhoit_liquid.getFreeEnergy(T_val[i]) / 1000., G_val[i], 0)
#####################################################

if __name__ == '__main__':
    suite = TestLoader().loadTestsFromTestCase(TestSoluteDatabase)
    TextTestRunner(verbosity=2).run(suite)
