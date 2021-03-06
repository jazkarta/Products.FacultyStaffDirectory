# -*- coding: utf-8 -*-

__author__ = """WebLion <support@weblion.psu.edu>"""
__docformat__ = 'plaintext'

from AccessControl import ClassSecurityInfo
from Acquisition import aq_inner, aq_parent
from Products.Archetypes.atapi import *
from Products.CMFCore.permissions import View
from Products.FacultyStaffDirectory.PersonGrouping import PersonGrouping
from Products.Relations.field import RelationField
from Products.FacultyStaffDirectory.config import *
from Products.CMFCore.utils import getToolByName
from Products.FacultyStaffDirectory.interfaces.department import IDepartment
from zope.interface import implements
from Products.FacultyStaffDirectory.permissions import ASSIGN_DEPARTMENTS_TO_PEOPLE
from Products.FacultyStaffDirectory import FSDMessageFactory as _

schema = Schema((

    RelationField(
        name='members',
        widget = RelatedItemsWidget(
            allow_search = True,
            allow_browse = True,
            show_indexes = False,
            force_close_on_insert = True,
            label = u"Members",
            label_msgid = "FacultyStaffDirectory_label_members",
            i18n_domain = "FacultyStaffDirectory",
            visible = {'edit' : 'visible', 'view' : 'visible' },
            pattern_options={
                'baseCriteria': [{
                    'i': 'portal_type',
                    'o': 'plone.app.querystring.operation.string.is',
                    'v': 'FSDPerson',
                }],
                'basePath': '',
                "contextPath": None,
                'selectableTypes': ['FSDPerson', ],
                'placeholder': _(u'Begin typing a name'),
            },
        ),
        write_permission=ASSIGN_DEPARTMENTS_TO_PEOPLE,
        allowed_types=('FSDPerson',),
        multiValued=1,
        relationship='departments_members'
    ),
),
)

Department_schema = getattr(PersonGrouping, 'schema', Schema(())).copy() + schema.copy()

class Department(PersonGrouping):
    """
    """
    security = ClassSecurityInfo()
    implements(IDepartment)
    _at_rename_after_creation = True
    meta_type = portal_type="FSDDepartment"
    schema = Department_schema   
    # Methods
    security.declareProtected(View, 'getMembershipInformation')
    def getMembershipInformation(self, person):
        """ Get the departmental membership information for a specific person
        """
        refCatalog = getToolByName(self, 'reference_catalog')
        refs = refCatalog.getReferences(self, 'departments_members', person)

        if not refs:
            return None
        else:
            return refs[0].getContentObject()

    security.declareProtected(View, 'getPeople')
    def getPeople(self):
        """ Return the people in this department.
            Mainly for context-sensitive classifications
        """
        return self.getMembers()
        
    security.declareProtected(View, 'getRawPeople')
    def getRawPeople(self):
        """ Return the people associations associated with this department
        """
        return self.getRawMembers()
    
    #
    # Validators
    #
    security.declarePrivate('validate_id')
    def validate_id(self, value):
        """Ensure the id is unique, also among groups globally
        """
        if value != self.getId():
            parent = aq_parent(aq_inner(self))
            if value in parent.objectIds():
                return "An object with id '%s' already exists in this folder" % value
        
            groups = getToolByName(self, 'portal_groups')
            if groups.getGroupById(value) is not None:
                return "A group with id '%s' already exists in the portal" % value
        
registerType(Department, PROJECTNAME)
# end of class Department
