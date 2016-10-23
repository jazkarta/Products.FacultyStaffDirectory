# -*- coding: utf-8 -*-

__author__ = """WebLion <support@weblion.psu.edu>"""
__docformat__ = 'plaintext'

#
# Test-cases for class(es) 
#

from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.FacultyStaffDirectory.config import *
from Products.FacultyStaffDirectory.tests.testPlone import testPlone
from Products.CMFCore.utils import getToolByName

class testFacultyStaffDirectory(testPlone):
    """Test-cases for class(es) ."""

    def afterSetUp(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def testFTISetup(self):
        """ Make sure the FTI is pulling info from the GS types profile """
        self.failUnless(self.portal.portal_types['FSDFacultyStaffDirectory'].Title() != "AT Content Type")

    def testGetSpecialtiesFolder(self):
        fsd = self.getPopulatedDirectory()
        specialtiesFolder = fsd.getSpecialtiesFolder()
        self.failUnless(specialtiesFolder.Title() == 'Specialties')
        self.failUnless(specialtiesFolder.Type() == 'Specialties Folder')

    def testDirectoryCreation(self):
        #Make sure the FacultyStaffDirectory was created
        self.portal.invokeFactory(type_name = "FSDFacultyStaffDirectory", id="test_directory")
        self.failUnless('test_directory' in self.portal.contentIds())

    def testDirectory_at_post_create(self):
        #Make sure the autogenerated content is properly created
        fsd = self.getPopulatedDirectory()
        #Check for autogenerated content
        self.failUnless('faculty' in fsd.contentIds())
        self.failUnless('staff' in fsd.contentIds())
        self.failUnless('grad-students' in fsd.contentIds())
        self.failUnless('committees' in fsd.contentIds())
        self.failUnless('specialties' in fsd.contentIds())

    def testGetClassifications(self):
        fsd = self.getPopulatedDirectory()
        classificationsBrains = fsd.getClassifications()
        self.failUnless('faculty' in [c.getObject().id for c in classificationsBrains])
        for c in classificationsBrains:
            self.failUnless(c.portal_type == 'FSDClassification')

    def testGetDepartments(self):
        fsd = self.getPopulatedDirectory()
        classificationsBrains = fsd.getDepartments()
        for c in classificationsBrains:
            self.failUnless(c.portal_type == 'FSDDepartment')


    def testGetPeople(self):
        fsd = self.getPopulatedDirectory()
        person = self.getPerson(id='abc123', firstName="Test", lastName="Person")        
        personList = fsd.getPeople()
        self.failUnless(person in personList)        
        for c in personList:
            self.failUnless(c.portal_type == 'FSDPerson')
        
    def testObjectReorder(self):
        fsd = self.getPopulatedDirectory()
        #Try to move a Classification to the top
        fsd.moveObjectsByDelta(['staff'], -100)
        self.failUnless(fsd.getObjectPosition('staff') == 0, "FSDClassification Subobject 'staff' should be at position 0.")
        fsd.moveObjectsByDelta(['committees'], -100)
        self.failUnless(fsd.getObjectPosition('committees') == 0, "FSDCommitteesFolder Subobject 'committees' should be at position 0.")
        fsd.moveObjectsByDelta(['specialties'], -100)
        self.failUnless(fsd.getObjectPosition('specialties') == 0, "FSDSpecialtiesFolder Subobject 'specialties' should be at position 0.")

    # tests for membrane integration
    def testFSDIsGroup(self):
        """Verify that FSDs are seen as groups
        """
        fsd = self.getPopulatedDirectory()
        self.failUnless(self.portal.portal_groups.getGroupById(fsd.id),"unable to find group with id of this fsd: %s" % fsd.id)
    
    # now test the functionality of the IGroup adapter (membership.facultystaffdirectory.py)
    def testIGroupAdapter(self):
        """Verify all methods of the IGroup adapter to the FacultyStaffDirectory content type
        """
        from Products.membrane.interfaces import IGroup
        from Products.CMFCore.utils import getToolByName
        
        fsd = self.getPopulatedDirectory()
        wf = getToolByName(fsd,'portal_workflow')
        
        #adapt to IGroup
        g = IGroup(fsd)
        
        #group title is the content object title
        fsd.setTitle("My FSD")
        self.failUnless(g.Title()=="My FSD")
        
        #roles are set on the object, but only available when object is published
        fsd.setRoles(('Reviewer',))
        # at first, object is 'visible', but not published, roles should be empty
        self.failIf('Reviewer' in g.getRoles(),"roles are active, but content unpublished\nRoles: %s\nReviewState: %s" % (g.getRoles(), wf.getInfoFor(fsd,'review_state')))
        #publish object
        wf.doActionFor(fsd,'publish')
        # now check again, role should be there
        self.failUnless('Reviewer' in g.getRoles(),"Roles not active, but content published\nRoles: %s\nReviewState: %s" % (g.getRoles(), wf.getInfoFor(fsd,'review_state')))
        
        # group id is set on content object, uniqueness is enforced elsewhere
        self.failUnless(g.getGroupId()==fsd.getId(),"getGroupId returning incorrect value:\nExpected: %s\nReceived: %s" % (fsd.getId(), g.getGroupId()))
        
        #members are obtained correctly
        self.person1 = self.getPerson(id='abc123', firstName="Test", lastName="Person")
        self.person2 = self.getPerson(id='def456', firstName="Testy", lastName="Persons")
        self.person3 = self.getPerson(id='ghi789', firstName="Tester", lastName="Personage")
        members = list(g.getGroupMembers())
        members.sort()
        self.failUnless(members == ['abc123','def456','ghi789'],"incorrect member list: %s" % members)
        
    def testValidateId(self):
        """Test that the validate_id validator works properly
        """
        from Products.CMFCore.utils import getToolByName
        
        # setup some content to test against
        fsd = self.getPopulatedDirectory()
        self.portal.invokeFactory('Document','doc1')
        pg = getToolByName(fsd,'portal_groups')
        pg.addGroup('group1');
        
        #allow unused id
        self.failUnless(fsd.validate_id('foo')==None,"failed to validate_id 'foo': %s" % fsd.validate_id('foo'))
        # allow current object id
        self.failUnless(fsd.validate_id('facultstaffdirectory')==None,"Failed to validate current id of fsd object: %s" % fsd.id)
        # deny id of other object in site
        self.failUnless('doc1' in fsd.validate_id('doc1'),"Allowed id 'doc1', even though there is an object with that id in the portal: %s" % fsd.validate_id('doc1'))
        # deny id of other group for site
        self.failUnless('group1' in fsd.validate_id('group1'),"Allowed id 'doc1', even though there is a group with that id in the portal: %s" % fsd.validate_id('group1'))
        
    def testFSDImpliesRoles(self):
        """Verify that published FSD provides roles to user, where unpublished FSD does not
        """
        #set up content
        self.directory = self.getPopulatedDirectory()
        self.person = self.getPerson(id='abc123', firstName="Test", lastName="Person")
        from Products.CMFCore.utils import getToolByName
        wf = getToolByName(self.directory,'portal_workflow')
        
        user = self.portal.portal_membership.getMemberById('abc123')
        # no roles on directory yet, should not find one in the global roles for user
        self.failIf('Reviewer' in user.getRolesInContext(self.portal),"roles from directory available on person, but directory roles unset %s" % user.getRolesInContext(self.portal))
        
        self.directory.setRoles(('Reviewer',))
        user = self.portal.portal_membership.getMemberById('abc123')
        # roles set,but directory is unpublished, should not find roles in global roles for user
        self.failIf('Reviewer' in user.getRolesInContext(self.portal),"roles from directory available on person, but directory unpublished %s" % user.getRolesInContext(self.portal))

        wf.doActionFor(self.directory,'publish')
        user = self.portal.portal_membership.getMemberById('abc123')
        self.failUnless('Reviewer' in user.getRolesInContext(self.portal),"roles from directory unavailable on person, but directory is published %s %s" % (user.getRolesInContext(self.portal),wf.getInfoFor(self.directory,'review_state')))
        
class testMultipleFacultyStaffDirectories(testPlone):
    """ Test that having more than one faculty staff directory in a site does not cause problems
    """

    def afterSetUp(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        # set up two directories
        self.fsd1 = self.getPopulatedDirectory(id="fsd1")
        self.fsd2 = self.getPopulatedDirectory(id="fsd2")
        # add a person in each directory
        self.person1 = self.getPerson(directory=self.fsd1, id='person1', firstName="A", lastName="Person")
        self.person2 = self.getPerson(directory=self.fsd2, id='person2', firstName="Another", lastName="Person")
        # add a specialty, department and classification to each
        self.fsd1.specialties.invokeFactory('FSDSpecialty', id="a-specialty", title="A Specialty")
        self.fsd1.committees.invokeFactory('FSDCommittee', id='a-committee', title='A Committee')
        self.fsd1.invokeFactory('FSDDepartment', id='a-department', title='A Department')
        self.fsd2.specialties.invokeFactory('FSDSpecialty', id="another-specialty", title="Another Specialty")
        self.fsd2.committees.invokeFactory('FSDCommittee', id='another-committee', title='Another Committee')
        self.fsd2.invokeFactory('FSDDepartment', id='another-department', title='Another Department')
    
    def getBaseQueryForWidget(self, obj, widget_name):
        """ return the base query for the reference browser widget on the field named by widget_name
            on the object obj
        """
        try:
            field = obj.schema[widget_name]
        except KeyError:
            self.fail('no field provided on %s named %s' % (obj, widget_name))
        else:
            widget = obj.schema[widget_name].widget
            return widget.getBaseQuery(obj, field)
            
    def executeBaseQueryAndCompare(self, query, cmpval):
        """ given a set of query parameters, exectute that query in the portal catalog, and 
            check the cmpval to verify it is _not_ in the list of things returned.
        """
        pc = getToolByName(self.portal, 'portal_catalog')
        results = pc(**query)
        id_list = [result.id for result in results]
        return cmpval in id_list
        
    def testFindOwnDirectoryPath(self):
        """ verify that the _get_parent_fsd_path method works correctly on people and 
            persongroupings
        """
        self.assertEqual('fsd1', self.person1._get_parent_fsd_path())
        self.assertEqual('fsd2', self.person2._get_parent_fsd_path())
        self.assertEqual('fsd1', self.fsd1['a-department']._get_parent_fsd_path())
        self.assertEqual('fsd2', self.fsd2['another-department']._get_parent_fsd_path())
        self.assertEqual('fsd1', self.fsd1.specialties['a-specialty']._get_parent_fsd_path())
        self.assertEqual('fsd2', self.fsd2.specialties['another-specialty']._get_parent_fsd_path())
        
    def testPersonRBWidgetBaseQuery(self):
        """ verify that the base query returned by the reference browser widget for various fields
            returns a query that results in the expected lists of content objects
        """
        # test the person specialties field
        base_query = self.getBaseQueryForWidget(self.person1, 'specialties')
        self.failUnless(self.executeBaseQueryAndCompare(base_query, 'a-specialty'))
        self.failIf(self.executeBaseQueryAndCompare(base_query, 'another-specialty'))
        
        # test the person departments field
        base_query = self.getBaseQueryForWidget(self.person1, 'departments')
        self.failUnless(self.executeBaseQueryAndCompare(base_query, 'a-department'))
        self.failIf(self.executeBaseQueryAndCompare(base_query, 'another-department'))
        
        # test the person committees field
        base_query = self.getBaseQueryForWidget(self.person1, 'committees')
        self.failUnless(self.executeBaseQueryAndCompare(base_query, 'a-committee'))
        self.failIf(self.executeBaseQueryAndCompare(base_query, 'another-committee'))
        
        # test the person assistants field
        base_query = self.getBaseQueryForWidget(self.person1, 'assistants')
        self.failUnless(self.executeBaseQueryAndCompare(base_query, 'person1'))
        self.failIf(self.executeBaseQueryAndCompare(base_query, 'person2'))
       
    def testPersonGroupingRBWidgetBaseQuery(self):
        """ verify that the base query returned by the reference browser widget for the people
            field of a person grouping returns a query that results in the expected list of
            FSDPerson objects
        """
        base_query = self.getBaseQueryForWidget(self.fsd1['a-department'], 'members')
        self.failUnless(self.executeBaseQueryAndCompare(base_query, 'person1'))
        self.failIf(self.executeBaseQueryAndCompare(base_query, 'person2'))
