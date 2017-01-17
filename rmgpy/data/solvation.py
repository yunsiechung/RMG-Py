#!/usr/bin/python
# -*- coding: utf-8 -*-

################################################################################
#
#   RMG - Reaction Mechanism Generator
#
#   Copyright (c) 2002-2010 Prof. William H. Green (whgreen@mit.edu) and the
#   RMG Team (rmg_dev@mit.edu)
#
#   Permission is hereby granted, free of charge, to any person obtaining a
#   copy of this software and associated documentation files (the 'Software'),
#   to deal in the Software without restriction, including without limitation
#   the rights to use, copy, modify, merge, publish, distribute, sublicense,
#   and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.
#
################################################################################

"""

"""

import os.path
import math
import logging
import numpy
import rmgpy.constants as constants
from rmgpy.species import Species
from copy import deepcopy
from base import Database, Entry, makeLogicNode, DatabaseError
from CoolProp.CoolProp import PropsSI
from rmgpy.thermo.nasa import NASA
import rmgpy.quantity as quantity

from rmgpy.molecule import Molecule, Atom, Bond, Group, atomTypes

################################################################################

def saveEntry(f, entry):
    """
    Write a Pythonic string representation of the given `entry` in the solvation
    database to the file object `f`.
    """
    f.write('entry(\n')
    f.write('    index = {0:d},\n'.format(entry.index))
    f.write('    label = "{0}",\n'.format(entry.label))
    
    if isinstance(entry.item, Molecule):
        if Molecule(SMILES=entry.item.toSMILES()).isIsomorphic(entry.item):
            # The SMILES representation accurately describes the molecule, so we can save it that way.
            f.write('    molecule = "{0}",\n'.format(entry.item.toSMILES()))
        else:
            f.write('    molecule = \n')
            f.write('"""\n')
            f.write(entry.item.toAdjacencyList(removeH=False))
            f.write('""",\n')
    elif isinstance(entry.item, Group):
        f.write('    group = \n')
        f.write('"""\n')
        f.write(entry.item.toAdjacencyList())
        f.write('""",\n')
    elif entry.item is not None:
        f.write('    group = "{0}",\n'.format(entry.item))
    
    if isinstance(entry.data, SoluteData):
        f.write('    solute = SoluteData(\n')
        f.write('        S = {0!r},\n'.format(entry.data.S))
        f.write('        B = {0!r},\n'.format(entry.data.B))
        f.write('        E = {0!r},\n'.format(entry.data.E))
        f.write('        L = {0!r},\n'.format(entry.data.L))
        f.write('        A = {0!r},\n'.format(entry.data.A))
        if entry.data.V is not None: f.write('        V = {0!r},\n'.format(entry.data.V))
        f.write('    ),\n')
    elif isinstance(entry.data, SolventData):
        f.write('    solvent = SolventData(\n')
        f.write('        s_g = {0!r},\n'.format(entry.data.s_g))
        f.write('        b_g = {0!r},\n'.format(entry.data.b_g))
        f.write('        e_g = {0!r},\n'.format(entry.data.e_g))
        f.write('        l_g = {0!r},\n'.format(entry.data.l_g))
        f.write('        a_g = {0!r},\n'.format(entry.data.a_g))
        f.write('        c_g = {0!r},\n'.format(entry.data.c_g))
        f.write('        s_h = {0!r},\n'.format(entry.data.s_h))
        f.write('        b_h = {0!r},\n'.format(entry.data.b_h))
        f.write('        e_h = {0!r},\n'.format(entry.data.e_h))
        f.write('        l_h = {0!r},\n'.format(entry.data.l_h))
        f.write('        a_h = {0!r},\n'.format(entry.data.a_h))
        f.write('        c_h = {0!r},\n'.format(entry.data.c_h))
        f.write('        A = {0!r},\n'.format(entry.data.A))
        f.write('        B = {0!r},\n'.format(entry.data.B))
        f.write('        C = {0!r},\n'.format(entry.data.C))
        f.write('        D = {0!r},\n'.format(entry.data.D))
        f.write('        E = {0!r},\n'.format(entry.data.E))
        f.write('        alpha = {0!r},\n'.format(entry.data.alpha))
        f.write('        beta = {0!r},\n'.format(entry.data.beta))
        f.write('        eps = {0!r},\n'.format(entry.data.eps))
        f.write('        inCoolProp = {0!r},\n'.format(entry.data.inCoolProp))
        f.write('        NameinCoolProp = "{0}",\n'.format(entry.data.NameinCoolProp))
        f.write('    ),\n')
    elif entry.data is None:
        f.write('    solute = None,\n')
    else:
        raise DatabaseError("Not sure how to save {0!r}".format(entry.data))
    
    f.write('    shortDesc = u"""')
    try:
        f.write(entry.shortDesc.encode('utf-8'))
    except:
        f.write(entry.shortDesc.strip().encode('ascii', 'ignore')+ "\n")
    f.write('""",\n')
    f.write('    longDesc = \n')
    f.write('u"""\n')
    try:
        f.write(entry.longDesc.strip().encode('utf-8') + "\n")    
    except:
        f.write(entry.longDesc.strip().encode('ascii', 'ignore')+ "\n")
    f.write('""",\n')

    f.write(')\n\n')

def generateOldLibraryEntry(data):
    """
    Return a list of values used to save entries to the old-style RMG
    thermo database based on the thermodynamics object `data`.
    """
    raise NotImplementedError()
    
def processOldLibraryEntry(data):
    """
    Process a list of parameters `data` as read from an old-style RMG
    thermo database, returning the corresponding thermodynamics object.
    """
    raise NotImplementedError()


class SolventData():
    """
    Stores Abraham/Mintz parameters for characterizing a solvent.
    """
    def __init__(self, s_h=None, b_h=None, e_h=None, l_h=None, a_h=None,
    c_h=None, s_g=None, b_g=None, e_g=None, l_g=None, a_g=None, c_g=None, A=None, B=None, 
    C=None, D=None, E=None, alpha=None, beta=None, eps=None, inCoolProp=False, NameinCoolProp=None):
        self.s_h = s_h
        self.b_h = b_h
        self.e_h = e_h
        self.l_h = l_h
        self.a_h = a_h
        self.c_h = c_h
        self.s_g = s_g
        self.b_g = b_g
        self.e_g = e_g
        self.l_g = l_g
        self.a_g = a_g
        self.c_g = c_g
        # These are parameters for calculating viscosity
        self.A = A
        self.B = B
        self.C = C
        self.D = D
        self.E = E
        # These are SOLUTE parameters used for intrinsic rate correction in H-abstraction rxns
        self.alpha = alpha
        self.beta = beta
        # This is the dielectric constant
        self.eps = eps
        # This describes the availability of the solvent data in CoolProp and its name in CoolProp
        self.inCoolProp = inCoolProp
        self.nameinCoolProp = NameinCoolProp
    
    def getHAbsCorrection(self):
        """
        If solvation is on, this will give the log10 of the ratio of the intrinsic rate
        constants log10(k_sol/k_gas) for H-abstraction rxns
        """
        return -8.3*self.alpha*self.beta
        
    def getSolventViscosity(self, T):
        """
        Returns the viscosity in Pa s, according to correlation in Perry's Handbook
        and coefficients in DIPPR
        """
        return math.exp(self.A + (self.B / T) + (self.C*math.log(T)) + (self.D * (T**self.E)))
                    
class SolvationCorrection():
    """
    Stores corrections for enthalpy, entropy, and Gibbs free energy when a species is solvated.
    Enthalpy and Gibbs free energy is in J/mol; entropy is in J/mol/K
    """
    def __init__(self, enthalpy=None, gibbs=None, entropy=None):
        self.enthalpy = enthalpy
        self.entropy = entropy
        self.gibbs = gibbs

class KfactorCoefficients():
    """
    Stores 4 coefficients (A, B, C, D) in the following K-factor relationships and
    the transition temperature (Ttransition) in K.
    1) 298 K <= T < Ttransition : Harvey's semi-empirical relationship
                    Tln(K-factor) = A + B*(1 + T/Tc)^(0.355) + C*T^(0.59)*exp(1 - T/Tc)
    2) Ttransition <= T < T_c : Japas and Levelt Sengers' linear relationship
                    Tln(K-factor) = D * (rho - rho_c)
    ** For details, see the documentation about Liquid Phase Systems **

    Relevant definitions:
    rho = molar density of the solvent [=] mol / m^3
    rho_c = critical molar density of the solvent [=] mol / m^3
    Tc = critical temperature of the solvent [=] K
    K-factor = y_solute / x_solute.
    y_solute = mole fraction of the solute in a gas phase at equilibrium in a binary dilute mixture
    x_solute = mole fraction of the solute at equilibrium in a binary dilute mixture
    """
    def __init__(self, A=None, B=None, C=None, D=None, Ttransition=None):
        self.lowTregion = [A, B, C]
        self.highTregion = D
        self.Ttransition = Ttransition
            
class SoluteData():
    """
    Stores Abraham parameters to characterize a solute
    """
    def __init__(self, S=None, B=None, E=None, L=None, A=None, V=None, comment=""):
        self.S = S
        self.B = B
        self.E = E
        self.L = L
        self.A = A
        self.V = V
        self.comment = comment
    def __repr__(self):
        return "SoluteData(S={0},B={1},E={2},L={3},A={4},comment={5!r})".format(self.S, self.B, self.E, self.L, self.A, self.comment)
    
    def getStokesDiffusivity(self, T, solventViscosity):
        """
        Get diffusivity of solute using the Stokes-Einstein sphere relation. 
        Radius is found from the McGowan volume.
        solventViscosity should be given in  kg/s/m which equals Pa.s
        (water is about 9e-4 Pa.s at 25C, propanol is 2e-3 Pa.s)
        Returns D in m2/s
        """
        radius = math.pow((75*self.V/constants.pi/constants.Na),(1.0/3.0))/100 # in meters, V is in MgGowan volume in cm3/mol/100
        D = constants.kB*T/6/constants.pi/solventViscosity/radius # m2/s
        return D  # m2/s
            
    def setMcGowanVolume(self, species):
        """
        Find and store the McGowan's Volume
        Returned volumes are in cm^3/mol/100 (see note below)
        See Table 2 in Abraham & McGowan, Chromatographia Vol. 23, No. 4, p. 243. April 1987
        doi: 10.1007/BF02311772
        
        "V is scaled to have similar values to the other
        descriptors by division by 100 and has units of (cm3mol−1/100)."
        the contibutions in this function are in cm3/mol, and the division by 100 is done at the very end.
        """
        molecule = species.molecule[0] # any will do, use the first.
        Vtot = 0

        for atom in molecule.atoms:
            thisV = 0.0
            if atom.isCarbon():
                thisV = 16.35
            elif (atom.element.number == 7): # nitrogen, do this way if we don't have an isElement method
                thisV = 14.39
            elif atom.isOxygen():
                thisV = 12.43
            elif atom.isHydrogen():
                thisV = 8.71
            elif (atom.element.number == 16):
                thisV = 22.91
            else:
                raise Exception()
            Vtot = Vtot + thisV

            for bond in molecule.getBonds(atom):
                # divide contribution in half since all bonds would be counted twice this way
                Vtot = Vtot - 6.56/2

        self.V= Vtot / 100; # division by 100 to get units correct.

################################################################################


################################################################################

class SolventLibrary(Database):
    """
    A class for working with a RMG solvent library.
    """
    def __init__(self, label='', name='', shortDesc='', longDesc=''):
        Database.__init__(self, label=label, name=name, shortDesc=shortDesc, longDesc=longDesc)

    def loadEntry(self,
                  index,
                  label,
                  solvent,
                  molecule=None,
                  reference=None,
                  referenceType='',
                  shortDesc='',
                  longDesc='',
                  ):
        spc = molecule
        if molecule is not None:
            try:
                spc = Species().fromSMILES(molecule)
            except:
                logging.debug("Solvent '{0}' does not have a valid SMILES '{1}'" .format(label, molecule))
                try:
                    spc = Species().fromAdjacencyList(molecule)
                except:
                    logging.error("Can't understand '{0}' in solute library '{1}'".format(molecule, self.name))
                    raise
            spc.generateResonanceIsomers()

        self.entries[label] = Entry(
            index = index,
            label = label,
            item = spc,
            data = solvent,
            reference = reference,
            referenceType = referenceType,
            shortDesc = shortDesc,
            longDesc = longDesc.strip(),
        )

    def load(self, path):
        """
        Load the solvent library from the given path
        """
        Database.load(self, path, local_context={'SolventData': SolventData}, global_context={})

    def saveEntry(self, f, entry):
        """
        Write the given `entry` in the solute database to the file object `f`.
        """
        return saveEntry(f, entry)
    
    def getSolventData(self, label):
        """
        Get a solvent's data from its name
        """
        return self.entries[label].data

    def getSolventStructure(self, label):
        """
        Get a solvent's molecular structure as SMILES or adjacency list from its name
        """
        return self.entries[label].item
        
class SoluteLibrary(Database):
    """
    A class for working with a RMG solute library. Not currently used.
    """
    def __init__(self, label='', name='', shortDesc='', longDesc=''):
        Database.__init__(self, label=label, name=name, shortDesc=shortDesc, longDesc=longDesc)

    def loadEntry(self,
                  index,
                  label,
                  molecule,
                  solute,
                  reference=None,
                  referenceType='',
                  shortDesc='',
                  longDesc='',
                  ):
        try:
            spc = Species().fromSMILES(molecule)
        except:
            logging.debug("Solute '{0}' does not have a valid SMILES '{1}'" .format(label, molecule))
            try:
                spc = Species().fromAdjacencyList(molecule)
            except:
                logging.error("Can't understand '{0}' in solute library '{1}'".format(molecule,self.name))
                raise

        self.entries[label] = Entry(
            index = index,
            label = label,
            item = spc,
            data = solute,
            reference = reference,
            referenceType = referenceType,
            shortDesc = shortDesc,
            longDesc = longDesc.strip(),
        )
    
    def load(self, path):
        """
        Load the solute library from the given path
        """
        Database.load(self, path, local_context={'SoluteData': SoluteData}, global_context={})

    def saveEntry(self, f, entry):
        """
        Write the given `entry` in the solute database to the file object `f`.
        """
        return saveEntry(f, entry)

    def generateOldLibraryEntry(self, data):
        """
        Return a list of values used to save entries to the old-style RMG
        thermo database based on the thermodynamics object `data`.
        """
        return generateOldLibraryEntry(data)

    def processOldLibraryEntry(self, data):
        """
        Process a list of parameters `data` as read from an old-style RMG
        thermo database, returning the corresponding thermodynamics object.
        """
        return processOldLibraryEntry(data)

################################################################################

class SoluteGroups(Database):
    """
    A class for working with an RMG solute group additivity database.
    """

    def __init__(self, label='', name='', shortDesc='', longDesc=''):
        Database.__init__(self, label=label, name=name, shortDesc=shortDesc, longDesc=longDesc)

    def loadEntry(self,
                  index,
                  label,
                  group,
                  solute,
                  reference=None,
                  referenceType='',
                  shortDesc='',
                  longDesc='',
                  ):
        if group[0:3].upper() == 'OR{' or group[0:4].upper() == 'AND{' or group[0:7].upper() == 'NOT OR{' or group[0:8].upper() == 'NOT AND{':
            item = makeLogicNode(group)
        else:
            item = Group().fromAdjacencyList(group)
        self.entries[label] = Entry(
            index = index,
            label = label,
            item = item,
            data = solute,
            reference = reference,
            referenceType = referenceType,
            shortDesc = shortDesc,
            longDesc = longDesc.strip(),
        )
    
    def saveEntry(self, f, entry):
        """
        Write the given `entry` in the thermo database to the file object `f`.
        """
        return saveEntry(f, entry)

    def generateOldLibraryEntry(self, data):
        """
        Return a list of values used to save entries to the old-style RMG
        thermo database based on the thermodynamics object `data`.
        """
        
        return generateOldLibraryEntry(data)

    def processOldLibraryEntry(self, data):
        """
        Process a list of parameters `data` as read from an old-style RMG
        thermo database, returning the corresponding thermodynamics object.
        """
        return processOldLibraryEntry(data)

################################################################################

class SolvationDatabase(object):
    """
    A class for working with the RMG solvation database.
    """

    def __init__(self):
        self.libraries = {}
        self.libraries['solvent'] = SolventLibrary()
        self.libraries['solute'] = SoluteLibrary()
        self.groups = {}
        self.local_context = {
            'SoluteData': SoluteData,
            'SolventData': SolventData
        }
        self.global_context = {}

    def __reduce__(self):
        """
        A helper function used when pickling a SolvationDatabase object.
        """
        d = {
            'libraries': self.libraries,
            'groups': self.groups,
            }
        return (SolvationDatabase, (), d)

    def __setstate__(self, d):
        """
        A helper function used when unpickling a SolvationDatabase object.
        """
        self.libraries = d['libraries']
        self.groups = d['groups']

    def load(self, path, libraries=None, depository=True):
        """
        Load the solvation database from the given `path` on disk, where `path`
        points to the top-level folder of the solvation database.
        
        Load the solvent and solute libraries, then the solute groups.
        """
        
        self.libraries['solvent'].load(os.path.join(path,'libraries','solvent.py'))
        self.libraries['solute'].load(os.path.join(path,'libraries','solute.py'))
         
        self.loadGroups(os.path.join(path, 'groups'))
        
    def getSolventData(self, solventName):
        try:
            solventData = self.libraries['solvent'].getSolventData(solventName)
        except:
            raise DatabaseError('Solvent {0!r} not found in database'.format(solventName))
        return solventData

    def getSolventStructure(self, solventName):
        try:
            solventStructure = self.libraries['solvent'].getSolventStructure(solventName)
        except:
            raise DatabaseError('Solvent {0!r} not found in database'.format(solventName))
        return solventStructure
        
    def loadGroups(self, path):
        """
        Load the solute database from the given `path` on disk, where `path`
        points to the top-level folder of the solute database.
        
        Three sets of groups for additivity, atom-centered ('abraham'), non atom-centered 
        ('nonacentered'), and radical corrections ('radical')
        """
        logging.info('Loading Platts additivity group database from {0}...'.format(path))
        self.groups = {}
        self.groups['abraham']   =   SoluteGroups(label='abraham').load(os.path.join(path, 'abraham.py'  ), self.local_context, self.global_context)
        self.groups['nonacentered']  =  SoluteGroups(label='nonacentered').load(os.path.join(path, 'nonacentered.py' ), self.local_context, self.global_context)
        self.groups['radical']  =  SoluteGroups(label='radical').load(os.path.join(path, 'radical.py' ), self.local_context, self.global_context)
   
    def save(self, path):
        """
        Save the solvation database to the given `path` on disk, where `path`
        points to the top-level folder of the solvation database.
        """
        path = os.path.abspath(path)
        if not os.path.exists(path): os.mkdir(path)
        self.saveLibraries(os.path.join(path, 'libraries'))
        self.saveGroups(os.path.join(path, 'groups'))

    def saveLibraries(self, path):
        """
        Save the solute libraries to the given `path` on disk, where `path`
        points to the top-level folder of the solute libraries.
        """
        if not os.path.exists(path): os.mkdir(path)
        for library in self.libraries.keys():
            self.libraries[library].save(os.path.join(path, library+'.py'))
        
    def saveGroups(self, path):
        """
        Save the solute groups to the given `path` on disk, where `path`
        points to the top-level folder of the solute groups.
        """
        if not os.path.exists(path): os.mkdir(path)
        for group in self.groups.keys():
            self.groups[group].save(os.path.join(path, group+'.py'))

    def loadOld(self, path):
        """
        Load the old RMG solute database from the given `path` on disk, where
        `path` points to the top-level folder of the old RMG database.
        """
        
        for (root, dirs, files) in os.walk(os.path.join(path, 'thermo_libraries')):
            if os.path.exists(os.path.join(root, 'Dictionary.txt')) and os.path.exists(os.path.join(root, 'Library.txt')):
                library = SoluteLibrary(label=os.path.basename(root), name=os.path.basename(root))
                library.loadOld(
                    dictstr = os.path.join(root, 'Dictionary.txt'),
                    treestr = '',
                    libstr = os.path.join(root, 'Library.txt'),
                    numParameters = 5,
                    numLabels = 1,
                    pattern = False,
                )
                library.label = os.path.basename(root)
                self.libraries[library.label] = library

        self.groups = {}
        self.groups['abraham'] = SoluteGroups(label='abraham', name='Platts Group Additivity Values for Abraham Solute Descriptors').loadOld(
            dictstr = os.path.join(path, 'thermo_groups', 'Abraham_Dictionary.txt'),
            treestr = os.path.join(path, 'thermo_groups', 'Abraham_Tree.txt'),
            libstr = os.path.join(path, 'thermo_groups', 'Abraham_Library.txt'),
            numParameters = 5,
            numLabels = 1,
            pattern = True,
        )

    def saveOld(self, path):
        """
        Save the old RMG Abraham database to the given `path` on disk, where
        `path` points to the top-level folder of the old RMG database.
        """
        # Depository not used in old database, so it is not saved

        librariesPath = os.path.join(path, 'thermo_libraries')
        if not os.path.exists(librariesPath): os.mkdir(librariesPath)
        for library in self.libraries.values():
            libraryPath = os.path.join(librariesPath, library.label)
            if not os.path.exists(libraryPath): os.mkdir(libraryPath)
            library.saveOld(
                dictstr = os.path.join(libraryPath, 'Dictionary.txt'),
                treestr = '',
                libstr = os.path.join(libraryPath, 'Library.txt'),
            )

        groupsPath = os.path.join(path, 'thermo_groups')
        if not os.path.exists(groupsPath): os.mkdir(groupsPath)
        self.groups['abraham'].saveOld(
            dictstr = os.path.join(groupsPath, 'Abraham_Dictionary.txt'),
            treestr = os.path.join(groupsPath, 'Abraham_Tree.txt'),
            libstr = os.path.join(groupsPath, 'Abraham_Library.txt'),
        )

    def getSoluteData(self, species):
        """
        Return the solute descriptors for a given :class:`Species`
        object `species`. This function first searches the loaded libraries
        in order, returning the first match found, before falling back to
        estimation via Platts group additivity.
        """
        soluteData = None
        
        # Check the library first
        soluteData = self.getSoluteDataFromLibrary(species, self.libraries['solute'])
        if soluteData is not None:
            assert len(soluteData)==3, "soluteData should be a tuple (soluteData, library, entry)"
            soluteData[0].comment += "Data from solute library"
            soluteData = soluteData[0]
        else:
            # Solute not found in any loaded libraries, so estimate
            soluteData = self.getSoluteDataFromGroups(species)
            # No Platts group additivity for V, so set using atom sizes
            soluteData.setMcGowanVolume(species)
        # Return the resulting solute parameters S, B, E, L, A
        return soluteData

    def getAllSoluteData(self, species):
        """
        Return all possible sets of Abraham solute descriptors for a given
        :class:`Species` object `species`. The hits from the library come
        first, then the group additivity  estimate. This method is useful
        for a generic search job. Right now, there should either be 1 or 
        2 sets of descriptors, depending on whether or not we have a 
        library entry.
        """
        soluteDataList = []
        
        # Data from solute library
        data = self.getSoluteDataFromLibrary(species, self.libraries['solute'])
        if data is not None: 
            assert len(data) == 3, "soluteData should be a tuple (soluteData, library, entry)"
            data[0].comment += "Data from solute library"
            soluteDataList.append(data)
        # Estimate from group additivity
        # Make it a tuple
        data = (self.getSoluteDataFromGroups(species), None, None)
        soluteDataList.append(data)
        return soluteDataList

    def getSoluteDataFromLibrary(self, species, library):
        """
        Return the set of Abraham solute descriptors corresponding to a given
        :class:`Species` object `species` from the specified solute
        `library`. If `library` is a string, the list of libraries is searched
        for a library with that name. If no match is found in that library,
        ``None`` is returned. If no corresponding library is found, a
        :class:`DatabaseError` is raised.
        """
        for label, entry in library.entries.iteritems():
            if species.isIsomorphic(entry.item) and entry.data is not None:
                return (deepcopy(entry.data), library, entry)
        return None

    def getSoluteDataFromGroups(self, species):
        """
        Return the set of Abraham solute parameters corresponding to a given
        :class:`Species` object `species` by estimation using the Platts group
        additivity method. If no group additivity values are loaded, a
        :class:`DatabaseError` is raised.
        
        It averages (linearly) over the desciptors for each Molecule (resonance isomer)
        in the Species.
        """       
        soluteData = SoluteData(0.0,0.0,0.0,0.0,0.0)
        count = 0
        comments = []
        for molecule in species.molecule:
            molecule.clearLabeledAtoms()
            molecule.updateAtomTypes()
            sdata = self.estimateSoluteViaGroupAdditivity(molecule)
            soluteData.S += sdata.S
            soluteData.B += sdata.B
            soluteData.E += sdata.E
            soluteData.L += sdata.L
            soluteData.A += sdata.A
            count += 1
            comments.append(sdata.comment)
        
        soluteData.S /= count
        soluteData.B /= count
        soluteData.E /= count
        soluteData.L /= count
        soluteData.A /= count
        
        # Print groups that are used for debugging purposes
        soluteData.comment = "Average of {0}".format(" and ".join(comments))

        return soluteData
   
    def transformLonePairs(self, molecule):
        """
        Changes lone pairs in a molecule to two radicals for purposes of finding
        solute data via group additivity. Transformed for each atom based on valency.
        """
        saturatedStruct = molecule.copy(deep=True)
        addedToPairs = {}

        for atom in saturatedStruct.atoms:
            addedToPairs[atom] = 0
            if atom.lonePairs > 0:
                charge = atom.charge # Record this so we can conserve it when checking
                bonds = saturatedStruct.getBonds(atom)
                sumBondOrders = 0
                for key, bond in bonds.iteritems():
                    if bond.order == 'S': sumBondOrders += 1
                    if bond.order == 'D': sumBondOrders += 2
                    if bond.order == 'T': sumBondOrders += 3
                    if bond.order == 'B': sumBondOrders += 1.5 # We should always have 2 'B' bonds (but what about Cbf?)
                if atomTypes['Val4'] in atom.atomType.generic: # Carbon, Silicon
                    while(atom.radicalElectrons + charge + sumBondOrders < 4):
                        atom.decrementLonePairs()
                        atom.incrementRadical()
                        atom.incrementRadical()
                        addedToPairs[atom] += 1
                if atomTypes['Val5'] in atom.atomType.generic: # Nitrogen
                    while(atom.radicalElectrons + charge + sumBondOrders < 3):
                        atom.decrementLonePairs()
                        atom.incrementRadical()
                        atom.incrementRadical()
                        addedToPairs[atom] += 1
                if atomTypes['Val6'] in atom.atomType.generic: # Oxygen, sulfur
                    while(atom.radicalElectrons + charge + sumBondOrders < 2):
                        atom.decrementLonePairs()
                        atom.incrementRadical()
                        atom.incrementRadical()
                        addedToPairs[atom] += 1
                if atomTypes['Val7'] in atom.atomType.generic: # Chlorine
                    while(atom.radicalElectrons + charge + sumBondOrders < 1):
                        atom.decrementLonePairs()
                        atom.incrementRadical()
                        atom.incrementRadical()
                        addedToPairs[atom] += 1

        saturatedStruct.update()
        saturatedStruct.updateLonePairs()
        
        return saturatedStruct, addedToPairs

    def removeHBonding(self, saturatedStruct, addedToRadicals, addedToPairs, soluteData):  
        
        # Remove hydrogen bonds and restore the radical
        for atom in addedToRadicals:
            for H, bond in addedToRadicals[atom]:
                saturatedStruct.removeBond(bond)
                saturatedStruct.removeAtom(H)
                atom.incrementRadical()

        # Change transformed lone pairs back
        for atom in addedToPairs:    
            if addedToPairs[atom] > 0:
                for pair in range(1, addedToPairs[atom]):
                    saturatedStruct.decrementRadical()
                    saturatedStruct.decrementRadical()
                    saturatedStruct.incrementLonePairs()

        # Update Abraham 'A' H-bonding parameter for unsaturated struct
        for atom in saturatedStruct.atoms:
            # Iterate over heavy (non-hydrogen) atoms
            if atom.isNonHydrogen() and atom.radicalElectrons > 0:
                for electron in range(1, atom.radicalElectrons):
                    # Get solute data for radical group    
                    try:
                        self.__addGroupSoluteData(soluteData, self.groups['radical'], saturatedStruct, {'*':atom})
                    except KeyError: pass
      
        return soluteData

    def estimateSoluteViaGroupAdditivity(self, molecule):
        """
        Return the set of Abraham solute parameters corresponding to a given
        :class:`Molecule` object `molecule` by estimation using the Platts' group
        additivity method. If no group additivity values are loaded, a
        :class:`DatabaseError` is raised.
        """
        # For thermo estimation we need the atoms to already be sorted because we
        # iterate over them; if the order changes during the iteration then we
        # will probably not visit the right atoms, and so will get the thermo wrong
        molecule.sortAtoms()

        # Create the SoluteData object with the intercepts from the Platts groups
        soluteData = SoluteData(
            S = 0.277,
            B = 0.071,
            E = 0.248,
            L = 0.13,
            A = 0.003
        )
        
        addedToRadicals = {} # Dictionary of key = atom, value = dictionary of {H atom: bond}
        addedToPairs = {} # Dictionary of key = atom, value = # lone pairs changed
        saturatedStruct = molecule.copy(deep=True)

        # Convert lone pairs to radicals, then saturate with H.
       
        # Change lone pairs to radicals based on valency
        if sum([atom.lonePairs for atom in saturatedStruct.atoms]) > 0: # molecule contains lone pairs
            saturatedStruct, addedToPairs = self.transformLonePairs(saturatedStruct)

        # Now saturate radicals with H
        if sum([atom.radicalElectrons for atom in saturatedStruct.atoms]) > 0: # radical species
            addedToRadicals = saturatedStruct.saturate()

        # Saturated structure should now have no unpaired electrons, and only "expected" lone pairs
        # based on the valency
        for atom in saturatedStruct.atoms:
            # Iterate over heavy (non-hydrogen) atoms
            if atom.isNonHydrogen():
                # Get initial solute data from main group database. Every atom must
                # be found in the main abraham database
                try:
                    self.__addGroupSoluteData(soluteData, self.groups['abraham'], saturatedStruct, {'*':atom})
                except KeyError:
                    logging.error("Couldn't find in main abraham database:")
                    logging.error(saturatedStruct)
                    logging.error(saturatedStruct.toAdjacencyList())
                    raise
                # Get solute data for non-atom centered groups (being found in this group
                # database is optional)    
                try:
                    self.__addGroupSoluteData(soluteData, self.groups['nonacentered'], saturatedStruct, {'*':atom})
                except KeyError: pass
        
        soluteData = self.removeHBonding(saturatedStruct, addedToRadicals, addedToPairs, soluteData)

        return soluteData

    def __addGroupSoluteData(self, soluteData, database, molecule, atom):
        """
        Determine the Platts group additivity solute data for the atom `atom`
        in the structure `structure`, and add it to the existing solute data
        `soluteData`.
        """

        node0 = database.descendTree(molecule, atom, None)

        if node0 is None:
            raise KeyError('Node not found in database.')

        # It's possible (and allowed) that items in the tree may not be in the
        # library, in which case we need to fall up the tree until we find an
        # ancestor that has an entry in the library
        node = node0
        
        while node is not None and node.data is None:
            node = node.parent
        if node is None:
            raise KeyError('Node has no parent with data in database.')
        data = node.data
        comment = node.label
        while isinstance(data, basestring) and data is not None:
            for entry in database.entries.values():
                if entry.label == data:
                    data = entry.data
                    comment = entry.label
                    break
        comment = '{0}({1})'.format(database.label, comment)

        # This code prints the hierarchy of the found node; useful for debugging
        #result = ''
        #while node is not None:
        #   result = ' -> ' + node + result
        #   node = database.tree.parent[node]
        #print result[4:]
        
        # Add solute data for each atom to the overall solute data for the molecule.
        soluteData.S += data.S
        soluteData.B += data.B
        soluteData.E += data.E
        soluteData.L += data.L
        soluteData.A += data.A
        soluteData.comment += comment + "+"
        
        return soluteData

    
    def calcH(self, soluteData, solventData):
        """
        Returns the enthalpy of solvation, at 298K, in J/mol
        """
        # Use Mintz parameters for solvents. Multiply by 1000 to go from kJ->J to maintain consistency
        delH = 1000*((soluteData.S*solventData.s_h)+(soluteData.B*solventData.b_h)+(soluteData.E*solventData.e_h)+(soluteData.L*solventData.l_h)+(soluteData.A*solventData.a_h)+solventData.c_h)  
        return delH
    
    def calcG(self, soluteData, solventData):
        """
        Returns the Gibbs free energy of solvation, at 298K, in J/mol
        """
        # Use Abraham parameters for solvents to get log K
        logK = (soluteData.S*solventData.s_g)+(soluteData.B*solventData.b_g)+(soluteData.E*solventData.e_g)+(soluteData.L*solventData.l_g)+(soluteData.A*solventData.a_g)+solventData.c_g
        # Convert to delG with units of J/mol
        delG = -constants.R*298*math.log(10.)*logK
        return delG
        
    def calcS(self, delG, delH):
        """
        Returns the entropy of solvation, at 298K, in J/mol/K
        """
        delS = (delH-delG)/298
        return delS
    
    def getSolvationCorrection298(self, soluteData, solventData):
        """ 
        Given a soluteData and solventData object, calculates the enthalpy, entropy,
        and Gibbs free energy of solvation at 298 K. Returns a SolvationCorrection
        object
        """
        correction = SolvationCorrection(0.0, 0.0, 0.0)
        correction.enthalpy = self.calcH(soluteData, solventData)
        correction.gibbs = self.calcG(soluteData, solventData)  
        correction.entropy = self.calcS(correction.gibbs, correction.enthalpy) 
        return correction

    def checkSolventStructure(self, solvent):
        """
        Check that the solventSpecies has the correct solventStructure.
        Database error is raised if the solventSpecies does not pass the isIsomorphic test with the solventStructure
        loaded from the solvent database
        """
        solventStructure = self.getSolventStructure(solvent.solventName)
        # If the old version of the database is used, solventStructure is None, so skip the check.
        if solventStructure:
            if not solvent.solventSpecies.isIsomorphic(solventStructure):
                raise DatabaseError('The molecular structure of the solvent {0!r} does not match the one from the solvent database.'
                                    ''.format(solvent.solventName))

    def getSolventTc(self, nameinCoolProp):
        """
        Given the solvent's name in CoolProp, it returns the critical temperature of the solvent in K
        """
        Tc = PropsSI('T_critical', nameinCoolProp)
        return Tc

    def getSolvationThermo(self, soluteData, solventData, gasWilhoit):
        """
        Given the soluteData, solventData, and gasWilhoit (gas phase thermo) objects,
        it applies the solvation correction to solute species and returns the Wilhoit and NASA
        objects for the solute's corrected thermo.
        This is used when the solvent can be found in CoolProp.
        """

        solventName = solventData.nameinCoolProp
        Tc = self.getSolventTc(solventName)
        Tlist = numpy.linspace(298., Tc, 7, True)
        dGsolvList = self.getSolvationFreeEnergy(soluteData, solventData, Tlist) # in J/mol
        dGgasList = [gasWilhoit.getFreeEnergy(T) for T in Tlist] # in J/mol
        dGcorrectedList = [dGsolvList[i] + dGgasList[i] for i in range(Tlist.shape[0])]
        correctedNASA = NASA().fitToFreeEnergyData(Tlist, numpy.asarray(dGcorrectedList), 298., Tc)
        correctedNASA.Cp0 = gasWilhoit.Cp0
        correctedNASA.CpInf = gasWilhoit.CpInf

        correctedWilhoit = correctedNASA.toWilhoit()
        correctedWilhoit.Tmin = quantity.ScalarQuantity(298., 'K')
        correctedWilhoit.Tmax = quantity.ScalarQuantity(Tc, 'K')

        return correctedWilhoit, correctedNASA

    def getSolvationFreeEnergy(self, soluteData, solventData, Tlist):
        """
        Given the instances of soluteData, solventData, and the temperature list, it returns
        the list of corresponding solvation gibbs free energy for the solute species in J/mol.

        Solvation free energy is calculated by using the following relationships:
        1) 298 K <= T < Ttransition : Harvey's semi-empirical relationship
                    Tln(K-factor) = A + B*(1 + T/Tc)^(0.355) + C*T^(0.59)*exp(1 - T/Tc)
        2) Ttransition <= T < T_c : Japas and Levelt Sengers' linear aymptotic relationship
                    Tln(K-factor) = D * (rho - rho_c)

        ** For details, see the documentation about Liquid Phase Systems **

        Relevant definitions:
        rho = molar density of the solvent [=] mol / m^3
        rho_c = critical molar density of the solvent [=] mol / m^3
        Tc = critical temperature of the solvent [=] K
        K-factor = y_solute / x_solute.
        y_solute = mole fraction of the solute in a gas phase at equilibrium in a binary dilute mixture
        x_solute = mole fraction of the solute at equilibrium in a binary dilute mixture
        Pvap = vapor pressure of the solvent [=] Pa
        """

        # 1. Find the optimal parameters
        KfactorCoeff = self.findSolvationParam(soluteData, solventData)
        A, B, C = KfactorCoeff.lowTregion
        D = KfactorCoeff.highTregion
        Ttransition = KfactorCoeff.Ttransition

        # 2. Calculate the K-factor in each temperature region using the optimized parameters.
        # Then convert K-factor into solvation free energy (dGsolv)
        solventName = solventData.nameinCoolProp
        Tc = self.getSolventTc(solventName) # critical temperature of the solvent, in K
        rhoc = PropsSI('rhomolar_critical', solventName) # the critical molar density of the solvent, in mol/m^3
        dGsolvList = []
        for T in Tlist:
            rho = PropsSI('Dmolar', 'T', T, 'Q', 0, solventName) # molar density of the solvent, in mol/m^3
            drho = rho - rhoc # rho - rho_c, in mol/m^3
            Pvap = PropsSI('P', 'T', T, 'Q', 0, solventName) # vapor pressure of the solvent, in Pa
            if T < Ttransition:
                Kfactor = math.exp((A + B*(1-T/Tc)**0.355 + C*math.exp(1-T/Tc)*T**0.59) / T)
            elif T == Tc:
                Kfactor = 1.
            else:
                Kfactor = math.exp(D * drho / T)
            # Calculate the solvation free energies from K-factor list. The formula is:
            # dGsolv(T) = R * T * ln( K-factor(T) * Pvap(T) / (R * T * rho(T)) )
            # The solvation free energy is evaluated at the saturation curve, so it is only a function of temperature.
            dGsolv = constants.R * T * math.log(Kfactor * Pvap / (constants.R * T * rho))
            dGsolvList.append(dGsolv) # in J/mol

        return dGsolvList

    def findSolvationParam(self, soluteData, solventData):
        """
        Given the soluteData and solventData objects, it finds the optimal parameters for the K-factor
        relationships. The parameters (A, B, C, D) are determined by enforcing the following equality constraints:
            1) x(298K, Harvery correlation) = x(298K, Abarham LSER)
            2) dx/dT (298K, Harvey correlation) = dx/dT (298K, Mintz LSER)
            3) x/dT (Transition, Harvey correlation) = x/dT (Ttransition, Japas and Levelt Sengers' correlation)
            4) x(Transition, Harvey correlation) = x(Ttransition, Japas and Levelt Sengers' correlation)
        where x = Tln(K-factor) in K. x is used in place of dGsolv to reduce calculation steps.
        Because Harvey's correlation is linear with respect to A, B, and C, its parameters can be
        directly calculated using the linear solver if the value of D is known. The optimal value of D is
        determined by using the nonlinear solver and minimizing the residual function.
        """

        # 1) Make an initial guess for D.
        # Use the Abraham and Mintz LSERs to extrapolate the K-factor at 350 K, an approximate upper
        # temperature limit for using the constant dHsolv and dSsolv assumptions.
        # Use the extrapolated point at 350 K and the critical limit of K-factor to find the make an
        # initial guess for D in the linear relationship of Tln(K-factor) = D * (rho - rho_c)
        solvationCorrection298 = self.getSolvationCorrection298(soluteData, solventData)
        dHsolv298 = solvationCorrection298.enthalpy # the enthalpy of solvation, at 298K, in J/mol
        dSsolv298 = solvationCorrection298.entropy # the entropy of solvation, at 298K, in J/mol/K
        solventName = solventData.nameinCoolProp
        rhoc = PropsSI('rhomolar_critical', solventName) # the critical molar density of the solvent, in mol/m^3
        Tlimit = 350. # the upper temperature limit for using the constant dHsolv and dSsolv assumptions
        rho = PropsSI('Dmolar', 'T', Tlimit, 'Q', 0, solventName)# the molar density of the solvent, in mol/m^3
        Pvap = PropsSI('P', 'T', Tlimit, 'Q', 0, solventName) # the vapor pressure of the solvent, in Pa
        dGsolvTlimit = dHsolv298 - Tlimit * dSsolv298 # extrapolated free energy of solvation, in J/mol
        K = math.exp(dGsolvTlimit / (Tlimit * constants.R)) / Pvap * constants.R * Tlimit * rho # K-factor
        x = Tlimit * math.log(K) # Tln(K-factor), in K
        guessD = x / (rho - rhoc) # slope of the linear relationship, in K*m^3/mol

        # 2. Find the optimal value of D from the initial guess using the residual function and
        # nonlinear solver
        Tc = self.getSolventTc(solventName)
        Ttransition = 298 + (Tc - 298)*0.35 # in K
        import scipy.optimize
        optimalD = scipy.optimize.fmin(self.getResidual, guessD, args=(soluteData, solventData, Tc, solventName, Ttransition,), disp=False)

        # 3. Find the remaining parameters, A, B, and C, by using the optimal value of D
        paramLowT = self.fitToHarveyForConstantD(soluteData, solventData, optimalD, Tc, solventName, Ttransition)
        KfactorCoeff = KfactorCoefficients()
        KfactorCoeff.lowTregion = paramLowT
        KfactorCoeff.highTregion = optimalD
        KfactorCoeff.Ttransition = Ttransition

        return KfactorCoeff

    def getResidual(self, D, soluteData, solventData, Tc, solventName, Ttransition):
        """
        Given the value of D, soluteData object, solventData object, solventData object, Tc, solventName,
        and Ttransition, it solves for the remaining parameters, A, B, and C, by using fitToHarveyForConstantD
        method and returns the residual of the following equality constraint:
            x(@Ttransition, Harvey correlation) = x(@Ttransition, Japas and Levelt Sengers' correlation)
        where x = Tln(K-factor) in K.
        """

        paramLowT = self.fitToHarveyForConstantD(soluteData, solventData, D, Tc, solventName, Ttransition)
        # Calculates Tln(K-factor) using the Harvey's correlation at Ttransition
        xTransition1 = paramLowT[0] + paramLowT[1]*(1-Ttransition/Tc)**0.355+paramLowT[2]*math.exp(1-Ttransition/Tc)*Ttransition**0.59
        # Calculates Tln(K-factor) using the Harvey's correlation at Ttransition
        rhoc = PropsSI('rhomolar_critical', solventName)
        rhoTransition = PropsSI('Dmolar', 'T', Ttransition, 'Q', 0, solventName)
        xTransition2 = D * (rhoTransition - rhoc)
        res = math.fabs(xTransition1 - xTransition2) # the residual must be an absolute value

        return res

    def fitToHarveyForConstantD(self, soluteData, solventData, D, Tc, solventName, Ttransition):
        """
        Given the value of D, soluteData object, solventData object, solventData object, Tc, solventName,
        and Ttransition, it solves for the remaining parameters, A, B, and C, by using the following
        equality constraints:
            1) x(298K, Harvery correlation) = x(298K, Abarham LSER)
            2) dx/dT (298K, Harvey correlation) = dx/dT (298K, Mintz LSER)
            3) dx/dT (Transition, Harvey correlation) = dx/dT (Ttransition, Japas and Levelt Sengers' correlation)
        where x = Tln(K-factor) in K.
        """

        # 1) Determine the terms in A matrix from the Harvey's semi-empirical correlation.
        T1 = 298. # in K
        T2 = 299. # in K
        Amatrix = numpy.array([[1, (1-T1/Tc)**0.355, math.exp(1-T1/Tc)*(T1**0.59)],
                    [0, -0.355/Tc * ((1-T2/Tc)**(-0.645)), math.exp(1-T2/Tc)*(0.59*T2**(-0.41)-T2**0.59/Tc)],
                   [0, -0.355/Tc * ((1-Ttransition/Tc)**(-0.645)), math.exp(1-Ttransition/Tc)*(0.59*Ttransition**(-0.41)-Ttransition**0.59/Tc)]])

        # 2) Determine the terms in b vector.
        # 2-1) Calculate Tln(K-factor) at 298 K using the Abraham LSER
        solvationCorrection298 = self.getSolvationCorrection298(soluteData, solventData)
        dGsolv298 = solvationCorrection298.gibbs # in J/mol
        dHsolv298 = solvationCorrection298.enthalpy # in J/mol
        dSsolv298 = solvationCorrection298.entropy # in J/mol/K
        rho298 = PropsSI('Dmolar', 'T', T1, 'Q', 0, solventName)
        Pvap298 = PropsSI('P', 'T', T1, 'Q', 0, solventName)
        K298 = math.exp(dGsolv298 / (T1 * constants.R)) / Pvap298 * constants.R * T1 * rho298
        x1 = T1 * math.log(K298) # Tln(K-factor) at 298 K, in K
        # 2-2) Calculate d(Tln(K-factor))/dT at 298K using the Mintz LSER.
        # The slope is estimated from the finite difference method with dT = 1 K
        dGsolvT2 = dHsolv298 - dSsolv298*T2
        rho2 = PropsSI('Dmolar', 'T', T2, 'Q', 0, solventName)
        Pvap2 = PropsSI('P', 'T', T2, 'Q', 0, solventName)
        K2 = math.exp(dGsolvT2 / (T2 * constants.R)) / Pvap2 * constants.R * T2 * rho2
        x2 = T2 * math.log(K2) # Tln(K-factor) at 299 K, in K
        slope298 = (x2-x1) / (T2-298.)
        # 2-3) Calculate d(Tln(K-factor))/dT at Ttransition using the Japas and Levelt Sengers' correlation
        # The slope is estimated from the finite difference method with dT = 1 K
        T4 = Ttransition + 1.
        rho3 = PropsSI('Dmolar', 'T', Ttransition, 'Q', 0, solventName)
        rho4 = PropsSI('Dmolar', 'T', T4, 'Q', 0, solventName)
        slopeTransition = D * (rho4-rho3) / (T4 - Ttransition)
        bvector = numpy.array([x1, slope298, slopeTransition])

        # 3) The parameters are calculated by solving: Ax = b
        parameters, residues, rank, s = numpy.linalg.lstsq(Amatrix, bvector)

        return parameters

    def getSolventThermo(self, solventData, gasWilhoit):
        """
        Given the solventData and gasWilhoit (gas phase thermo) objects,
        it applies the solvation correction to solvent species and returns the Wilhoit and NASA
        objects for the corrected solvent thermo.
        This is used if the solvent can be found in CoolProp.
        """

        solventName = solventData.nameinCoolProp
        Tc = self.getSolventTc(solventName)
        Tlist = numpy.linspace(298., Tc, 7, True)
        dGsolvList = self.getSelfSolvationFreeEnergy(solventData, Tlist) # J/mol
        dGgasList = [gasWilhoit.getFreeEnergy(T) for T in Tlist] # J/mol
        dGcorrectedList = [dGsolvList[i] + dGgasList[i] for i in range(Tlist.shape[0])]
        correctedNASA = NASA().fitToFreeEnergyData(Tlist, numpy.asarray(dGcorrectedList), 298., Tc)
        correctedNASA.Cp0 = gasWilhoit.Cp0
        correctedNASA.CpInf = gasWilhoit.CpInf

        correctedWilhoit = correctedNASA.toWilhoit()
        correctedWilhoit.Tmin = quantity.ScalarQuantity(298., 'K')
        correctedWilhoit.Tmax = quantity.ScalarQuantity(Tc, 'K')

        return correctedWilhoit, correctedNASA

    def getSelfSolvationFreeEnergy(self, solventData, Tlist):
        """
        Given the instances of solventData and the temperature list, it returns the
        list of solvation gibbs free energy in J/mol at each temperature for the solvent species.
        The solvation free energy of the solvent species can be directly computed from
        their gas-liquid partition coefficients (equilibrium ratio of the gas and liquid
        phase concentration) obtained from CoolProp.
        """

        solventName = solventData.nameinCoolProp
        Tc = self.getSolventTc(solventName) # critical temperature of the solvent, in K
        dGsolvList = [] # in J/mol
        for T in Tlist:
            if T == Tc:
                dGsolvList.append(0.) # for solvent species, the solvation free energy approaches zero as T approaches Tc
            else:
                rhoGas = PropsSI('Dmolar', 'T', T, 'Q', 1, solventName) # gas phase molar density (concentration) in mol/m^3
                rhoLiquid = PropsSI('Dmolar', 'T', T, 'Q', 0, solventName) # liquid phase molar density (concentration) in mol/m^3
                dGsolv = constants.R * T * math.log( rhoGas / rhoLiquid ) # in J/mol
                dGsolvList.append(dGsolv)

        return dGsolvList