# -*- coding: utf-8 -*-

__author__ = """WebLion <support@weblion.psu.edu>"""
__docformat__ = 'plaintext'

#
# Test-cases for class(es) Person
#

import os
from zope.component import getUtility
from Products.CMFCore.utils import getToolByName
from Products.membrane.interfaces import IUserAuthentication
from Products.FacultyStaffDirectory.config import *
from Products.FacultyStaffDirectory.tests.base import FacultyStaffDirectoryTestCase
from Products.FacultyStaffDirectory.tests.base import PACKAGE_HOME
from Products.FacultyStaffDirectory.interfaces import IConfiguration
from plone.app.relations.interfaces import IRelationshipSource, IRelationshipTarget
from plone.relations.interfaces import IContextAwareRelationship

def loadImage(name, size=0):
    """Load image from testing directory."""
    path = os.path.join(PACKAGE_HOME, 'input', name)
    fd = open(path, 'rb')
    data = fd.read()
    fd.close()
    return data

# Grab images for testing
TEST_GIF = loadImage('testUserPhoto.gif')
TEST_GIF_LEN = len(TEST_GIF)
TEST_JPEG = loadImage('testUserPhoto.jpg')
TEST_JPEG_LEN = len(TEST_JPEG)
TEST_TIFF = loadImage('testUserPhoto.tif')
TEST_TIFF_LEN = len(TEST_TIFF)

class testPerson(FacultyStaffDirectoryTestCase):
    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.directory = self.getPopulatedDirectory()
        self.person = self.getPerson(id='abc123', firstName="Test", lastName="Person")
    
    def simulateATGUIInteraction(self, person=None, task='create'):
        if not person:
            person = self.person
        allowed_tasks = ['edit', 'create',]
        if task not in allowed_tasks:
            raise ValueError, 'parameter "task" must be one of %s' % allowed_tasks
        else:
            person.reindexObject()
            try:
                my_task = allowed_tasks.index(task)
            except ValueError:
                raise ValueError, '%s not in list of approved GUI tasks' % task
            
            if my_task==0:
                person.at_post_edit_script()
            elif my_task==1:
                person.at_post_create_script()
    
    def _testAssistantOwnershipAfter(self, person=None, task='create'):
        """boilerplate for testing making an assistant owner after a gui task"""
        if not person:
            person = self.person
        
        newperson = self.getPerson(id='def456', firstName="Test", lastName="Assistant")
        person.setAssistants([newperson.UID(),])
        self.simulateATGUIInteraction(person=person, task=task)
        owners = person.users_with_local_role('Owner')
        
        return 'def456' in owners
    

class testWithoutSpecialties(testPerson):
#     def afterSetUp(self):
#         testPerson.afterSetUp(self)
#         FunctionalTestSetup().setUp()
#
#     def beforeTearDown(self):
#         FunctionalTestSetup().tearDown()
#         testPerson.beforeTearDown(self)
    
    def testCreatePerson(self):
        # Make sure the Title override is working
        self.failUnlessEqual(self.person.Title(), u"Test Person")
        
        # Check the sortable name
        self.failUnlessEqual(self.person.getSortableName(), ('person', 'test'))
        
        # Check that Personnel Managers can add a Person.
        self.logout()
        self.login()
        self.setRoles(['Personnel Manager'])
        try:
            self.getPerson(id='zif572', firstName="Test", lastName="Person")
        except 'Unauthorized': 
            self.fail("User with the Personnel Manager role was unable to create a Person.")
    
    def testCourses(self):
        """Add and retrieve course objects"""
        self.person.invokeFactory(type_name="FSDCourse", id="test-course")
        self.failUnless('test-course' in self.person.contentIds())
        self.failUnless('test-course' in [c.id for c in self.person.getCourses()])
    
    # def testAssignClassifications(self):
    #     """Assign classifications to a person"""
    #     classifications = [c.UID for c in self.directory.getClassifications()]
    #     self.person.setClassifications(classifications)
    #     for c in self.person.getClassifications():
    #         self.failUnless(c.id in ['faculty', 'staff', 'grad-students'])
    #         self.failUnlessEqual(c.Type(), 'Classification')
            
    def testAssignPersonGroupings(self):
        """ assign person groupings to a person
        """
        groupings = [g.UID for g in self.directory.getPersonGroupings()]
        self.person.setGroupings(groupings)
        for g in self.person.getGroupings():
            self.failUnless(g.id in ['faculty', 'staff', 'grad-students'])
            self.failUnlessEqual(g.Type(), 'Person Grouping')
    
    def testAssignAssistants(self):
        """Assign an assistant to a person"""
        newperson = self.getPerson(id='def456', firstName="Test", lastName="Assistant")
        self.person.setAssistants([newperson.UID(),])
        for a in self.person.getAssistants():
            self.failUnless(a.id == 'def456', 'wrong id for assistant, wanted "def456", got %s' % a.id)
            self.failUnlessEqual(a.Type(), 'Person')
            self.failUnlessEqual(a.getReferences(relationship="assistants_people")[0].id, "abc123")
    
    def testMiddleName(self):
        #add a middle name
        self.person.setMiddleName('Joe')
        
        #title should change
        self.failUnlessEqual(self.person.Title(), u"Test Joe Person")
        
        #but sortable name shouldn't
        self.failUnlessEqual(self.person.getSortableName(), ('person', 'test'))
    
    def testSuffix(self):
        #Add a suffix
        self.person.setSuffix('WTF')
        
        #Title should change
        self.failUnlessEqual(self.person.Title(), u"Test Person, WTF")
        
        #But Sortable Name shouldn't
        self.failUnlessEqual(self.person.getSortableName(), ('person', 'test'))
    
    def testAllNameParts(self):
        #Add a suffix
        self.person.setSuffix('WTF')
        #Add a middle name
        self.person.setMiddleName('Joe')
        
        #Title should change
        self.failUnlessEqual(self.person.Title(), u"Test Joe Person, WTF")
        
        #But Sortable Name shouldn't
        self.failUnlessEqual(self.person.getSortableName(), ('person', 'test'))
    
    def testSortableName(self):
        self.directory.invokeFactory('FSDPerson', id='a1', firstName = 'Albert', lastName='Williams', classifications=['faculty'])
        self.directory.invokeFactory('FSDPerson', id='b2', firstName = 'Albert', lastName='von Whatsit', classifications=['faculty'])
        self.directory.invokeFactory('FSDPerson', id='c3', firstName = 'Albert', lastName="d'Example", classifications=['faculty'])
        sortedPeople = self.directory['faculty'].getSortedPeople()
    
    # ems174: I can't get this test to consistently add and check unicode titles. Any thoughts?
    #def testPersonTitleUnicode(self):
    #    """Make sure the Title accessor override properly handles unicode"""
    #    id = self.directory.invokeFactory('Person', id='def123', firstName=u'BjÃ¶rk', lastName=u'BjÃžrn')
    #    self.failUnlessEqual(self.directory[id].Title(), u'BjÃ¶rk BjÃžrn')
    
    def testPhoneNumberValidation(self):
        """Make sure we're validating the phone number based on the regex in the configlet."""
        
        fsd_tool = getUtility(IConfiguration)
        desc = fsd_tool.phoneNumberDescription
        self.failUnless(self.person.validate_officePhone('(555) 555-5555') is None)
        self.failUnlessEqual(self.person.validate_officePhone('555 555-5555'), "Please provide the phone number in the format %s" % desc)
        
        # Make sure a blank value for the phone number results in no validation
        self.failUnless(self.person.validate_officePhone('') is None, "A blank value for officePhone should not be validated since officePhone is not a required field.")
        
        # Make sure a blank value for the regex results in no validation.
        fsd_tool.phoneNumberRegex = u''
        self.failUnless(self.person.validate_officePhone('555 555-5555') is None, "A blank value for phoneNumberRegex should result in any value being accepted")
    
    def testImageHandling(self):
        """Make sure that image upload and display are handled properly."""
        
        pm = getToolByName(self.portal, 'portal_membership')
        #make sure the person's member portrait isn't defined
        self.failUnlessEqual(pm.getPersonalPortrait('abc123').__name__, 'defaultUser.gif')
        
        # Delete the (nonexistant) image, make sure the portrait stays undefined
        self.person.setImage('DELETE_IMAGE')
        self.failUnlessEqual(pm.getPersonalPortrait('abc123').__name__, 'defaultUser.gif')
        
        self.person.setImage(TEST_GIF, content_type="image/gif")
        #self.failUnlessEqual(self.person.getImage().data, TEST_GIF)
        # Try to get a 10x10 version of the image
        imageOfSizeTag = self.person.getImageOfSize(10, 10)
        self.failUnlessEqual(imageOfSizeTag, '<img src="http://nohost/plone/facstaffdirectory/abc123/image" alt="Test Person" title="Test Person" height="10" width="10" />')
        self.failUnlessEqual(pm.getPersonalPortrait('abc123').__name__, 'image')
        
        # Try to get a scaled-by-ratio image with a width of 100.
        scaledImageTag = self.person.getScaledImageByWidth(100)
        self.failUnlessEqual(scaledImageTag, '<img src="http://nohost/plone/facstaffdirectory/abc123/image" alt="Test Person" title="Test Person" height="150" width="100" />')
        
        # Delete the image, make sure the portrait is deleted as well
        self.person.setImage('DELETE_IMAGE')
        self.failUnlessEqual(pm.getPersonalPortrait('abc123').__name__, 'defaultUser.gif')
        
        #self.person.setImage(TEST_JPEG, content_type="image/jpeg")
        #self.failUnlessEqual(self.person.getImage().data, TEST_JPEG)
        
        self.person.setImage(TEST_TIFF, content_type="image/tiff")
        #self.failUnlessEqual(self.person.getImage().data, TEST_TIFF)
        # Try to get a 10x10 version of the image
        imageOfSizeTag = self.person.getImageOfSize(10, 10)
        self.failUnlessEqual(imageOfSizeTag, '<img src="http://nohost/plone/facstaffdirectory/abc123/image" alt="Test Person" title="Test Person" height="10" width="10" />')
        
        # Try to get a scaled-by-ratio image with a width of 100.
        # TIFF handling in Plone is broken (probably the fault of PIL), handle the problem nicely.
        scaledImageTag = self.person.getScaledImageByWidth(100)
        self.failUnless(scaledImageTag == '<img src="http://nohost/plone/facstaffdirectory/abc123/image" alt="Test Person" title="Test Person" height="150" width="100" />' or scaledImageTag == '')
        
    
    def testNoDefaultSchemata(self):
        """We've got custom schemata in here, and we don't want the default. Make sure nobody's
           put one back in."""
        self.failUnless('default' not in self.person.schema.getSchemataNames())
    
    def testFTISetup(self):
        """Make sure the FTI is pulling info from the GS types profile"""
        self.failUnless(self.portal.portal_types['FSDPerson'].Title() != "AT Content Type")
    
    def testObjectReorder(self):
        """Make sure we can reorder objects within this folderish Person."""
        self.person.invokeFactory(type_name="FSDCourse", id="course1")
        self.person.invokeFactory(type_name="FSDCourse", id="course2")
        self.person.invokeFactory(type_name="FSDCourse", id="course3")
        self.person.moveObjectsByDelta(['course3'], -100)
        self.failUnless(self.person.getObjectPosition('course3') == 0, "FSDCourse Subobject 'course3' should be at position 0.")
    
    ## More tests for membrane stuff
    def testPersonIsUser(self):
        """Make sure a person can be found by portal_membership."""
        member = self.portal.portal_membership.getMemberById('abc123')
        self.failUnless(member,"%s" % member)
    
    def testIPerson(self):
        """Make sure that the id and fullname returned are correct."""
        # The id is obtained from the person object directly, uniqueness is enforced
        id = self.person.id
        self.failUnlessEqual(id, 'abc123', "Person object returned incorrect id.")
    
    def testIUserRelated(self):
        """Test the functionality of the IUserRelated interface."""
        from Products.membrane.interfaces import IUserRelated
        # adapt the person object
        u = IUserRelated(self.person)
        uid = u.getUserId()
        self.failUnlessEqual(uid, 'abc123', "incorrect value for getUserId")
    
    def testIUserAuthentication(self):
        """Test the functionality of the IUserAuthentication interface."""
        # adapt the person object
        u = IUserAuthentication(self.person)
        uname = u.getUserName()
        self.failUnlessEqual(uname, 'abc123', "incorrect value for getUserName.")
        
        fsd_tool = getUtility(IConfiguration)
        if fsd_tool.useInternalPassword:
            self.person.setPassword("chewy1")
            self.failIf(u.verifyCredentials(    {                                    }), "somehow verified empty credentials")
            self.failIf(u.verifyCredentials(    {'login':'abc123','password':''      }), "verified missing password")
            self.failIf(u.verifyCredentials(    {'login':'',      'password':'chewy1'}), "verified missing login")
            self.failIf(u.verifyCredentials(    {'login':'harry1','password':'chewy1'}), "verified incorrect login")
            self.failIf(u.verifyCredentials(    {'login':'abc123','password':'chewy2'}), "verified incorrect password")
            self.failIf(u.verifyCredentials(    {'login':'harry1','password':'chewy2'}), "verified incorrect login and password")
            self.failUnless(u.verifyCredentials({'login':'abc123','password':'chewy1'}), "failed to verify correct login and password")
        else:
            self.failIf(u.verifyCredentials({'login':'abc123','password':'chewy1'}), "internal password not used, method should return none.  Value returned: %s" % returnval)
    
    def testLogin(self):
        """Test that a Person can log in."""
        mt = self.portal.portal_membership
        self.logout()
        self.login('abc123')
        member = mt.getAuthenticatedMember()
        self.failUnlessEqual(member.id, 'abc123', msg="incorrect user logged in: %s" % member)
    
    def testOwnershipAfterCreate(self):
        """Test that a user owns his/her Person object when created."""
        self.simulateATGUIInteraction(task='create')
        self.failUnlessEqual(self.person.getOwnerTuple()[1], 'abc123')
    
    def testAssistantOwnershipAfterCreate(self):
        """Test that named assistants get ownership of a person object when it is created"""
        self.failUnless(self._testAssistantOwnershipAfter(task='create'), "designated assistant is not listed as an owner")
    
    def testOwnershipAfterEdit(self):
        """Test that a user owns his/her Person object after editing."""
        self.simulateATGUIInteraction(task='edit')
        self.failUnlessEqual(self.person.getOwnerTuple()[1], 'abc123')
    
    def testAssistantOwnershipAfterEdit(self):
        """Test that named assistants get ownership of a person object when it is edited"""
        self.failUnless(self._testAssistantOwnershipAfter(task='edit'), "designated assistant is not listed as an owner")
        
    def testMultipleUserPrefRoleAssignment(self):
        """Test for regression on https://weblion.psu.edu/trac/weblion/ticket/711"""
        self.simulateATGUIInteraction(task='create')
        self.simulateATGUIInteraction(task='edit')
        perms = list(self.person.get_local_roles_for_userid('abc123'))
        self.failUnlessEqual(perms.count('User Preferences Editor'), 1, "the role 'User Preferences Editor' is listed more than once after multiple GUI interactions")
        
    def testAssistantDoesNotGetUserPrefRole(self):
        """Test to ensure that the assigned assistant does not have the 'User Preferences Editor' role"""
        self._testAssistantOwnershipAfter(task="create")
        self.failIf('def456' in self.person.users_with_local_role('User Preferences Editor'), "Assistant can edit user prefs after create")
        self.simulateATGUIInteraction(task="edit")
        self.failIf('def456' in self.person.users_with_local_role('User Preferences Editor'), "Assistant can edit user prefs after edit") 
        
    
    def testValidateId(self):
        """Test that the validate_id method enforces uniqueness for person id."""
        #create a different person and try to use their id
        self.directory.invokeFactory(type_name="FSDPerson",id="def456",firstName="Joe",lastName="Blow")
        self.failUnless('def456' in self.person.validate_id('def456'))
        #create a different content object and try to use its id
        self.directory.invokeFactory("Document", "mydoc")
        self.failUnless('mydoc' in self.person.validate_id('mydoc'))
    
    def testValidateWebsites(self):
        """Test that the url validation is working correctly."""
        # Get the sequence validator used by the 'websites' field
        val = self.person.schema['websites'].validators[1][0]
        self.failIfEqual(val(['www.foo.com']), 1, 'Validator should be checking for a full URL (including the http:// prefix'')')
        self.failIfEqual(val(['http://www.foo.com', 'www.foo.com']), 1, 'Validator should be checking for a full URL (including the http:// prefix) in all values of a lines field.')
        self.failUnlessEqual(val(['http://www.foo.com', 'http://bar.com']), 1, 'Validator should check multiple urls and pass if all are valid.')
    
    def testVCard(self):
        self.person.setOfficeCity(u'München')
        expectedUnicodeOutput = "M\xc3\xbcnchen"
        self.failUnless(expectedUnicodeOutput in self.person.vcard_view(self.app.REQUEST, self.app.REQUEST.response), "Improperly handled unicode in vCard output.")
    
    def _testIdWriteAccess(self):
        """Utility function to support testing write access to the ID attribute of a person
            
        Just log in as some user with a given role with respect to self.person and run this
        Function with no arguments.
        
        """
        from Products.CMFCore.utils import getToolByName
        mt = getToolByName(self.portal, 'portal_membership')
        user = mt.getAuthenticatedMember()
        perm = self.person.schema.get('id').write_permission
        return user.checkPermission(perm, self.person)
    
    def testIdWriteAccessForManager(self):
        self.logout()
        self.loginAsPortalOwner()
        self.failUnless(self._testIdWriteAccess(), 'Manager does not have write access to ID property of FSDPerson object')
    
    def testIdWriteAccessForOwner(self):
        self.logout()
        self.login(self.person.id)
        self.failIf(self._testIdWriteAccess(), 'Owner has write access to ID property of FSDPerson object')
    
    def testIdWriteAccessForAnonymous(self):
        self.logout()
        self.failIf(self._testIdWriteAccess(), 'Anonymous has write access to ID property of FSDPerson object')
    
    def testIMembraneUserManagement(self):
        """Test the functionality of the IMembraneUserManagement interface."""
        from Products.membrane.interfaces import IMembraneUserManagement, IUserAuthentication
        
        user = IMembraneUserManagement(self.person);
        auth = IUserAuthentication(self.person);
        
        #test setting password directly, verify that verifyCredentials works as expected
        fsd_tool = getUtility(IConfiguration)
        self.person.setPassword('secret1')
        if fsd_tool.useInternalPassword:
            self.failUnless(auth.verifyCredentials({'login':'abc123','password':'secret1'}), "failed to verify correct login and password, setting password directly")
        else:
            self.failIf(auth.verifyCredentials({'login':'abc123','password':'secret1'}), "internal password not used, method should return none, setting password directly.  Value returned: %s" % returnval)
        
        # now set password using the userChanger method and verify that it worked
        user.doChangeUser('abc123', 'secret2')
        fsd_tool = getUtility(IConfiguration)
        if fsd_tool.useInternalPassword:
            self.failUnless(auth.verifyCredentials({'login':'abc123','password':'secret2'}), "failed to verify correct login and password, testing doChangeUser()")
        else:
            self.failIf(auth.verifyCredentials({'login':'abc123','password':'secret2'}), "internal password not used, method should return none, testing doChangeUser().  Value returned: %s" % returnval)
        
        # set password and some other value with doChangeUser, using keywords
        self.failIf(self.person.getEmail(), "email already set, and it shouldn't be: %s" % self.person.getEmail())
        user.doChangeUser('abc123','secret', email='joebob@hotmail.com')
        self.failUnlessEqual(self.person.getEmail(), 'joebob@hotmail.com', msg="failed to update email via doChangeUser(): %s" % self.person.getEmail())
        
        # now try to delete the user
        self.failUnless(hasattr(self.directory,'abc123'), "directory does not have person")
        user.doDeleteUser('abc123')
        self.failIf(hasattr(self.directory,'abc123'), "directory still contains person")
        
        # we should not be able to log in as this person anymore
        self.logout()
        try:
            self.login('abc123')
        except AttributeError:
            pass
        else:
            self.fail("still able to login: %s" % self.portal.portal_membership.getAuthenticatedMember().id)
    
    def testTurnOffMembership(self):
        """Make sure Persons still work after disabling membership support."""
        fsd_tool = getUtility(IConfiguration)
        # Disable membership support for FSDPerson
        fsd_tool.enableMembraneTypes = set([t for t in fsd_tool.enableMembraneTypes if t != 'FSDPerson'])
        # Double check to make sure that FSDPerson is really detatched from membrane
        userFolder = getToolByName(self.portal, 'acl_users')
        self.failIf(userFolder.getUserById('abc123'))
        
        # Try to add a new person
        self.directory.invokeFactory(type_name="FSDPerson", id="eee555", firstName="Ima", lastName="Personobject")
        person = self.directory['eee555']
        # Manually run the at_post_create_script to fire the PersonModifiedEvent.
        try:
            person.at_post_create_script()
        except KeyError:
            self.Fail("FacultyStaffDirectory incorrectly tried to find the user attached to a FSPerson while membrane support was disabled.")

    def testMemberSearch(self):
        """Make sure that membrane is using the right fields for member searches."""
        self.directory.invokeFactory(type_name="FSDPerson", id="cvf092", firstName="Another", lastName="Testperson")
        self.directory.invokeFactory(type_name="FSDPerson", id="ope593", firstName="Somebody", lastName="Altogetherdifferent")

        pas = getToolByName(self.portal, "acl_users")
        searchParams = {'fullname':'Test'}
        results = pas.searchUsers(**searchParams)
        self.failUnless(len(results) == 2, "Search did not return the right number of members. Expected 2, got %s." % len(results))
        self.failUnless('cvf092' in [a['id'] for a in results], "Expected member cvf092 to be in the search results.")

    # Err... can't actually test for this since it's being handled in pre_edit_setup. Any ideas?
    # def testDefaultEditor(self):
    #     """Make sure the editor is being set to the site's default."""
    #     memberProps = getToolByName(self.portal, 'portal_memberdata')
    #     defaultEditor = memberProps.wysiwyg_editor
    #     self.assertEquals(self.person.getUserpref_wysiwyg_editor(), defaultEditor, 'The editor set by default for Person does not follow the site default.')


    ## End tests for membrane stuff

class testWithSpecialties(testPerson):
    def afterSetUp(self):
        testPerson.afterSetUp(self)  # logs in as portal owner. Yuck.
        self._makeAndAssignSpecialties()

        # Make sure stuff is readable by Anonymous, so we can run tests as him:
        workflowTool = getToolByName(self.portal, 'portal_workflow')
        for o in [self.directory]:
            workflowTool.doActionFor(o, 'publish')
        self.logout()  # Run as Anonymous to make sure getResearchTopics is anonymously callable. (bug #384)

    def _makeAndAssignSpecialties(self):
        """Make a bunch of specialties, publish them, and assign them all to the test person."""
        def makeSpecialties(node, container, explicitSpecialties):
            """Make specialties inside `container` according to the tree-shaped dict `node`. Append the created specialties (unless marked as {'associated': False}) to the list `explicitSpecialties`."""
            for child in node.get('children', []):
                id = child['id']
                container.invokeFactory(type_name='FSDPersonGrouping', id=id, title=child['title'])
                newSpecialty = container[id]
                if child.get('associated', True):
                    explicitSpecialties.append(newSpecialty)
                makeSpecialties(child, newSpecialty, explicitSpecialties)

        # Create specialties:
        explicitSpecialties = []
        makeSpecialties({'children':
            [{'id': 'sanitation', 'title': 'Sanitation', 'children':
                [{'id': 'picking-stuff-up', 'title': 'Picking stuff up'},
                 {'id': 'hosing-stuff-down', 'title': 'Hosing stuff off'},
                 {'id': 'keeping-stuff-from-getting-so-messed-up-to-begin-with', 'title': 'Keeping stuff from getting so dirty in the first place'}]},
             {'id': 'mastication', 'title': 'Mastication', 'associated': False, 'children':
                [{'id': 'chomping', 'title': 'Chomping'}]}]}, self.directory, explicitSpecialties)
                
        
        # Assign them to the person:
        self.person.setGroupings([s.UID() for s in explicitSpecialties])

        # Add a research topic for Sanitation:
        sanitationRefObj = self.person.getGroupingAssociationContent(target=self.directory['sanitation'])[0]
        sanitationRefObj.setText('Picking up sprockets from bowls of soup.')
        
    def testSpecialties(self):
        """Test various accessors related to the Specialties tree."""
        # Make sure getSpecialties() returns the specialties in the other they occur in the SpecialtiesFolder(s). Also indirectly (but sufficiently) test getSpecialtyTree():
        self.failUnlessEqual([x.id for x in self.person.getGroupings()], ['sanitation', 'picking-stuff-up', 'hosing-stuff-down', 'keeping-stuff-from-getting-so-messed-up-to-begin-with', 'chomping'])

        # Assert getSpecialtyNames() works:
        #self.failUnlessEqual(self.person.getSpecialtyNames(), ['Sanitation', 'Picking stuff up', 'Hosing stuff off', 'Keeping stuff from getting so dirty in the first place', 'Chomping'])

        # Make sure getResearchTopics() works and is anonymously callable (that is, #384 hasn't regressed). (testWithSpecialties' tests run as Anonymous.):
        #self.failUnlessEqual(self.person.getResearchTopics(), ['<p>Picking up sprockets from bowls of soup</p>'])

        # Make sure that the various indexes have been updated (see #325).
        #indexDataBeforeReindex = self.portal.portal_catalog.getIndexDataForUID('/'.join(self.person.getPhysicalPath()))
        #rawSpecialtiesBeforeReindex = indexDataBeforeReindex['getRawSpecialties']
        #self.person.reindexObject()
        #indexDataAfterReindex = self.portal.portal_catalog.getIndexDataForUID('/'.join(self.person.getPhysicalPath()))
        #rawSpecialtiesAfterReindex = indexDataAfterReindex['getRawSpecialties']
        #self.failUnlessEqual(rawSpecialtiesBeforeReindex, rawSpecialtiesAfterReindex)

    def testAssociationContentCreatedWithGroupingAsTarget(self):
        """ Ensure that AssociationContent objects are created when the relationship is initiated from the Person end. """

        self.loginAsPortalOwner()
        self.directory.invokeFactory(type_name='FSDPersonGrouping', id='grpng', title='Useless Grouping')
        grpng = self.directory.grpng
        self.person.setGroupings([grpng.UID()])

        source = IRelationshipSource(self.person)
        rel = list(source.getRelationships(relation='PersonGroupingAssociation', target=grpng))[0]
        obj = IContextAwareRelationship(rel).getContext()
        self.failUnless(obj, "AssociationContent object not created when a Person->PersonGrouping relationship was created.")
        
    def testAssociationContentCreatedWithPersonAsTarget(self):
        """ Ensure that AssociationContent objects was are created when the relationship is initiated from the PersonGrouping end. """
        self.loginAsPortalOwner()
        self.directory.invokeFactory(type_name='FSDPersonGrouping', id='grpng', title='Useless Grouping')
        grpng = self.directory.grpng
        grpng.setPeople([self.person.UID()])
        source = IRelationshipTarget(grpng)
        rel = list(source.getRelationships(relation='PersonGroupingAssociation', source=self.person))[0]
        try:
            obj = IContextAwareRelationship(rel).getContext()
        except TypeError:
            self.fail('Unable to adapt PersonGrouping->Person relationship to IContextAwareRelationship. AssociationContent object not created.')
        self.failUnless(obj, "AssociationContent object was not created when a PersonGrouping->Person relationship was created.")

    def testAssociationContentDeletedWhenRelationshipRemovedOnGroupingEnd(self):
        """ Ensure that AssociationContent objects are deleted when the relationship is deleted on the PersonGrouping end. 
        """
        # Create a grouping, relate it to our Person.
        self.loginAsPortalOwner()
        self.directory.invokeFactory(type_name='FSDPersonGrouping', id='grpng', title='Useless Grouping')
        grpng = self.directory.grpng
        self.person.setGroupings([grpng.UID()])
        
        # Get the AssocationContent object.
        source = IRelationshipSource(self.person)
        rel = list(source.getRelationships(relation='PersonGroupingAssociation', target=grpng))[0]
        obj = IContextAwareRelationship(rel).getContext()
        
        objId = obj.id

        grpng.setPeople([])
        self.failIf(objId in self.person.at_references.objectIds(), "AssociationContent object not deleted when the relationship is removed from the PersonGrouping end.")
        

    def testAssociationContentDeletedWhenGroupingDeleted(self):
        """ Ensure that AssociationContent objects are deleted when the PersonGrouping is deleted. 
            We can assume that the reverse is true since the AssociationContent is stored within the Person.
        """
        # Create a grouping, relate it to our Person.
        self.loginAsPortalOwner()
        self.directory.invokeFactory(type_name='FSDPersonGrouping', id='grpng', title='Useless Grouping')
        grpng = self.directory.grpng
        self.person.setGroupings([grpng.UID()])
        
        # Get the AssocationContent object.
        source = IRelationshipSource(self.person)
        rel = list(source.getRelationships(relation='PersonGroupingAssociation', target=grpng))[0]
        obj = IContextAwareRelationship(rel).getContext()
        objId = obj.id
        
        # Delete the grouping
        self.directory.manage_delObjects(['grpng'])
        self.failIf(objId in self.person.at_references.objectIds(), "AssociationContent object not deleted when the related PersonGrouping object is deleted.")
        
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testWithoutSpecialties))
    suite.addTest(makeSuite(testWithSpecialties))
    return suite
