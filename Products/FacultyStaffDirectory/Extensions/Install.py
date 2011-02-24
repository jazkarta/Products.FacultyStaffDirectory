# -*- coding: utf-8 -*-

__author__ = """WebLion <support@weblion.psu.edu>"""
__docformat__ = 'plaintext'
import os.path
import sys
from StringIO import StringIO
from sets import Set
from App.Common import package_home
from Products.CMFCore.utils import getToolByName

from Products.Archetypes.atapi import listTypes
from Products.FacultyStaffDirectory.config import PROJECTNAME
from Products.FacultyStaffDirectory.config import product_globals as GLOBALS
from Products.FacultyStaffDirectory.config import ADDITIONAL_CATALOG_INDEXES
from Products.FacultyStaffDirectory.config import ADDITIONAL_CATALOG_METADATA
from Products.membrane.config import TOOLNAME as MEMBRANE_TOOL

originalMyFolderActionId = "mystuff"
newMyFolderActionId = "fsdmystuff"
originalProfileActionId = "MemberPrefs"
newProfileActionId = "fsdMemberPrefs"

def install(self, reinstall=False):
    """ External Method to install FacultyStaffDirectory """
    
    out = StringIO()
    print >> out, "Installation log of %s:" % PROJECTNAME

    portal = getToolByName(self,'portal_url').getPortalObject()
    quickinstaller = portal.portal_quickinstaller
    
    def importProfiles(self, importContexts):
        """Import all steps from the GenericSetup profiles listen in `importContexts`."""
        setupTool = getToolByName(self, 'portal_setup')
        for eachContext in importContexts:
            setupTool.runAllImportStepsFromProfile(eachContext)

    profilesToImport = ('profile-Products.FacultyStaffDirectory:default',)

    importProfiles(self, profilesToImport)

    print >> out, "Ran all GS import steps." 
    
    # configuration for Relations
    relations_tool = getToolByName(self,'relations_library')
    xmlpath = os.path.join(package_home(GLOBALS),'relations.xml')
    f = open(xmlpath)
    xml = f.read()
    f.close()
    relations_tool.importXML(xml)
    
    # Install the product tool:
    if not hasattr(self, 'facultystaffdirectory_tool'):
        addTool = self.manage_addProduct['FacultyStaffDirectory'].manage_addTool
        addTool('FSDFacultyStaffDirectoryTool')

    #####
    # Catalog Manipulations
    #  These could be places in a catalog.xml GenericSetup step, but doing so would
    #  mean that the added indexes would be deleted each time we re-install.  This
    #  would slow down reinstalls unacceptably.  Leave this code here in install.py
    catalogTool = getToolByName(self, 'portal_catalog')
    
    # Add indexes if they don't exist:
    for indexName, indexType in ADDITIONAL_CATALOG_INDEXES:
        if indexName not in catalogTool.indexes():
             catalogTool.addIndex(indexName, indexType)

    # Add metadata fields if they don't exist:
    for fieldName in ADDITIONAL_CATALOG_METADATA:
        if fieldName not in catalogTool.schema():
            catalogTool.addColumn(fieldName)    
            
    # Since our content types don't exist on first install, there's nothing to index
    # And even then, we only need to update the FSD objects
    # But then again, if we do an uninstall/install, we need to do this. Let's just do it 
    # all the time since it won't find anything on first installation anyway.
    indexes = [indexName for indexName, indexType in ADDITIONAL_CATALOG_INDEXES]
    FSDTypes = [t['meta_type'] for t in listTypes(PROJECTNAME)]
    for brain in catalogTool(portal_type=FSDTypes):
        try:
            brain.getObject().reindexObject(indexes)
        except KeyError:
            # Relations content objects seem to not be able to handle getObject(), 
            # but the data doesn't seem to get lost, so just ignore it.
            pass
    #####
    # Smart Folder Manipulations
    #  These could be places in a catalog.xml GenericSetup step, but doing so would
    #  mean that the added indexes would be deleted each time we re-install.  This
    #  would slow down reinstalls unacceptably.  Leave this code here in install.py
    
    # Set up SmartFolder/Topic/Collection fields:
    smart_folder_tool = getToolByName(self, 'portal_atct')           
    
    # add smart folder indexes if needed
    def addSmartFolderIndex(indexName, friendlyName, description, criteria):
        try:
            smart_folder_tool.removeIndex(indexName)
        except:
            pass
        smart_folder_tool.addIndex(indexName, friendlyName, description, enabled=True, criteria=criteria)
    
    addSmartFolderIndex("getRawClassifications", "Classification", "The classification assigned to a person", criteria=['ATReferenceCriterion'])
    addSmartFolderIndex("getRawSpecialties", "Specialty", "A person's listed specialty areas", criteria=['ATReferenceCriterion'])
    addSmartFolderIndex("getRawCommittees", "Committee", "A person's listed committees", criteria=['ATReferenceCriterion'])
    addSmartFolderIndex("getRawPeople", "People", "The people assigned to a person grouping (ie committee, department, specialty, classification)", criteria=['ATReferenceCriterion'])
    addSmartFolderIndex("getRawDepartments", "Department", "The departments assigned to a person", criteria=['ATReferenceCriterion'])
    addSmartFolderIndex("getSortableName", "Full Name", "The person's name, last name first", criteria=['ATListCriterion'])
    
    def addSmartFolderMetadata(columnName, friendlyName, description, enabled):
        try:
            smart_folder_tool.removeMetadata(columnName)
        except:
            pass
        smart_folder_tool.addMetadata(columnName, friendlyName, description, enabled=True)
    
    addSmartFolderMetadata("getCommitteeNames", "Committees", "The committees with which the person is associated", enabled=True)
    addSmartFolderMetadata("getDepartmentNames", "Departments", "The departments with which the person is associated", enabled=True)
    addSmartFolderMetadata("getSpecialtyNames", "Specialties", "The specialties with which the person is associated", enabled=True)
    addSmartFolderMetadata("getClassificationNames", "Classifications", "The classifications with which the person is associated", enabled=True)
    addSmartFolderMetadata("getResearchTopics", "Research Topics", "The research topics with which the person is associated", enabled=True)
    
    #####
    # Set up the NavTree
    #   can this be done through GS?  If so, move it there.
    mtntl = list(self.portal_properties.navtree_properties.metaTypesNotToList)
    metaTypes = ['FSDCourse', 'FSDPerson', 'FSDFacultyStaffDirectoryTool']
    for mType in metaTypes: 
        if not mType in mtntl:
            mtntl.append(mType)
    self.portal_properties.navtree_properties._p_changed=1
    self.portal_properties.navtree_properties.metaTypesNotToList=tuple(mtntl)
    
    #####
    # Action Manipulations
    #   These should probably also live in GS profiles, eventually.  Move them there if possible
    #   This should be movable after we drop support for plone 2.5
        
    # Add action icon for vCards:
    ai=getToolByName(self, 'portal_actionicons')
    try:
        ai.getActionInfo('plone','vcard')
    except KeyError:
        # Action icon doesn't exist. Add it.
        ai.addActionIcon('plone', 'vcard', 'vcard.png', 'vCard export')
    
    # Fixing the 'MyFolder' action
    # massage the membership tool actions to make 'mystuff' invisible,
    # This allows the one we added in GS to take its place silently.
    actionsTool = getToolByName(self, 'portal_actions')
    actions = actionsTool.listActions()
    for action in actions:
        if action.id == originalMyFolderActionId:
            action.visible = False
    
    # now move the new my folder action up to the top of the list
    orderedFolder = actionsTool.user
    orderedFolder.manage_move_objects_to_top(None,(newMyFolderActionId,))
        
    # Fixing the 'MemberPrefs' action
    # massage the portal_controlpanel tool to make MemberPrefs invisible
    cp = getToolByName(self, 'portal_controlpanel')
    currentActions = cp.listActions()
    for action in currentActions:
        if action.id == originalProfileActionId:
            action.visible = False

    # Register a configlet to control some behaviors of the product:
    if "FacultyStaffDirectory" not in [ c.id for c in cp._actions ]:
        cp.registerConfiglet(
            "FacultyStaffDirectory",
            "Faculty/Staff Directory",
            "string:${portal_url}/facultystaffdirectory_tool/",
            category="Products",
            permission="Manage portal",
            appId="FacultyStaffDirectory",
            imageUrl="group.png")
        
    # Set up revisioning, if available:
    if hasattr(self,'portal_repository'):
        cp = getToolByName(self, "portal_repository")
        existing = cp.getVersionableContentTypes()
        new = existing + ['FSDPerson', 'FSDCommittee', 'FSDSpecialty']
        cp.setVersionableContentTypes(new)

    # Refresh the membrane_tool catalog. Otherwise, our content disappears from the user db on refresh
    # however, rebuilding the entire catalog is a bit excessive, and kills installs on sites with large FSDs, let's do the reindex thing instead
    membraneTool = getToolByName(self, 'membrane_tool')
    membraneIndexes = membraneTool.indexes()
    membraneTool.manage_reindexIndex(membraneIndexes)
    
    # Unindex the FSD tool so it doesn't show up in our folder contents
    fsdTool = getToolByName(self, 'facultystaffdirectory_tool')
    fsdTool.unindexObject()
    
    return out.getvalue()

def uninstall(self, reinstall=False):
    out = StringIO()
    def uninstallProfiles(portal):
        setup_tool = getToolByName(portal, 'portal_setup')
        setupTool.runAllImportStepsFromProfile('profile-FacultyStaffDirectory:uninstall')  # doesn't exist in Plone 2.5
        
    # don't do things we don't need to do on reinstall
    if not reinstall:
    
        # Remove classes from NavTree_properties:
        mtntl = list(self.portal_properties.navtree_properties.metaTypesNotToList)
        metaTypes = ['FSDCourse', 'FSDPerson', 'FSDFacultyStaffDirectoryTool']
        for mType in metaTypes: 
            if mType in self.portal_properties.navtree_properties.metaTypesNotToList:
                mtntl.remove(mType)
        self.portal_properties.navtree_properties._p_changed=1
        self.portal_properties.navtree_properties.metaTypesNotToList = tuple(mtntl)
        
        # uninstall the vcard action icon
        ai=getToolByName(self, 'portal_actionicons')
        try:
            ai.removeActionIcon('plone', 'vcard')
        except KeyError:
            #Icon doesn't exist, problem solved.
            pass
        
        #####
        # Undo Catalog Adjustments
        catalogTool = getToolByName(self, 'portal_catalog')
                
        # remove additional indexes
        for indexName, indexType in ADDITIONAL_CATALOG_INDEXES:
            if indexName in catalogTool.indexes():
                catalogTool.delIndex(indexName)
                
        # remove additional metadata fields
        for fieldName in ADDITIONAL_CATALOG_METADATA:
            if fieldName in catalogTool.schema():
                catalogTool.delColumn(fieldName)
                
        #####
        # Undo Smart Folder Adjustments
        #  Note:  It appears that these steps do not need to be taken.  Apparently, removing
        #         the indexes and metadata from the catalog tool itself is enough to ensure 
        #         that they are also removed from the smart folder tool.
        #  Update: It turns out that this code is needed in plone 3.x  If it is missing, 
        #          the indexes and metadata do not get removed.  there must be some change in 
        #          the relationship between the smart folder tool and the portal catalog
        smart_folder_tool = getToolByName(self, 'portal_atct')           

        # Remove SmartFolder indexes
        def removeSmartFolderIndex(indexName):
            try:
                smart_folder_tool.removeIndex(indexName)
            except:
                pass
        
        for i in ['getSortableName', 'getRawClassifications', 'getRawCommittees', 'getRawSpecialties', 'getRawDepartments', 'getRawPeople']:
            removeSmartFolderIndex(i)
        
        # remove SmartFolder metadata too
        def removeSmartFolderMetadata(columnName):
            # Remove existing indexes if there are some
            try:
                smart_folder_tool.removeMetadata(columnName)
            except:
                pass
                
        for f in ["getCommitteeNames", "getDepartmentNames", "getSpecialtyNames", "getClassificationNames", "getResearchTopics"]:
            removeSmartFolderMetadata(f)

        
        # massage the membership tool actions to make 'mystuff' visible,
        # at the same time, remove the action we created via GS profile
        tool = getToolByName(self, 'portal_actions')
        currentActions = tool.listActions()
        index = 0
        for action in currentActions:
            if action.id == originalMyFolderActionId:
                action.visible = True
            if action.id == newMyFolderActionId:
                tool.deleteActions([index])
            index += 1
        
        # massage the portal_controlpanel tool to make MemberPrefs visible
        # at the same time, delete the action we created via GS Profile
        cp = getToolByName(self, 'portal_controlpanel')
        currentActions = cp.listActions()
        index = 0
        for action in currentActions:
            if action.id == originalProfileActionId:
                action.visible = True
            if action.id == newProfileActionId:
                cp.deleteActions([index])
            index += 1
        
        # remove the FSD configlet from the portal control panel
        if "FacultyStaffDirectory" in [ c.id for c in cp._actions ]:
            cp.unregisterConfiglet("FacultyStaffDirectory")

        # Tear down revisioning, if available:
        if hasattr(self,'portal_repository'):
            pr = getToolByName(self, "portal_repository")
            existing = pr.getVersionableContentTypes()
            new = []
            for type in existing:
                if type not in ['FSDPerson', 'FSDCommittee', 'FSDSpecialty']:
                    new.append(type)
            pr.setVersionableContentTypes(new)

        # Okay, unregister the membrane_tool from the InstalledProduct.portalobjects property in the QI tool.
        # IMPORTANT!!!
        # remember that this is all because of the way we are installing membrane in the 
        # first place, when the QI tool is improved in all versions to support installing 
        # via GS profile alone, this will be moot.  It shouldn't break even then, though, 
        # because of the set stuff.
        qt = getToolByName(self, 'portal_quickinstaller')
        fsd_product = getattr(qt, 'FacultyStaffDirectory')
        portal_objects_list = fsd_product.getPortalObjects()
        pol_set = set(portal_objects_list)
        removal_set = set([MEMBRANE_TOOL])
        fsd_product.portalobjects = tuple(pol_set - removal_set)

    return out.getvalue()
