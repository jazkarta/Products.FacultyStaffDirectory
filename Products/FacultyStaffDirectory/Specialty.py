# -*- coding: utf-8 -*-

__author__ = """WebLion <support@weblion.psu.edu>"""
__docformat__ = 'plaintext'

from AccessControl import ClassSecurityInfo
from Products.Archetypes import atapi
from Products.Relations.field import RelationField
from Products.FacultyStaffDirectory import config
from Products.FacultyStaffDirectory.PersonGrouping import PersonGrouping
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName

from Products.FacultyStaffDirectory.interfaces.specialty import ISpecialty
from Products.FacultyStaffDirectory.permissions import ASSIGN_SPECIALTIES_TO_PEOPLE

from zope.interface import implements
from Products.FacultyStaffDirectory import FSDMessageFactory as _

try:
    from Products.Archetypes.Widget import TinyMCEWidget
except ImportError:
    TinyMCEWidget = atapi.RichWidget


schema = atapi.Schema((

    RelationField(
        name='people',
        widget = atapi.RelatedItemsWidget(
            allow_search = True,
            allow_browse = True,
            show_indexes = False,
            force_close_on_insert = True,
            label = u"People",
            label_msgid = "FacultyStaffDirectory_label_people",
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
        write_permission=ASSIGN_SPECIALTIES_TO_PEOPLE,
        allowed_types=('FSDPerson',),
        multiValued=True,
        relationship='SpecialtyInformation'  # weird relationship name is ArchGenXML's fault
    ),

    atapi.ImageField(
        name='overviewImage',
        schemata='Overview',
        widget=atapi.ImageWidget(
            label=_(u"FacultyStaffDirectory_label_overview_image",
                    default=u"Overview image (used for specialty overview view)"),
            i18n_domain='FacultyStaffDirectory',
            default_content_type='image/gif',
        ),
        storage=atapi.AttributeStorage(),
        original_size=(200, 200),
        sizes={'normal': (200, 250)},
        default_output_type='image/jpeg',
        allowable_content_types=('image/gif', 'image/jpeg', 'image/png'),
    ),

    atapi.TextField(
        name='overviewText',
        schemata='Overview',
        allowable_content_types=config.ALLOWABLE_CONTENT_TYPES,
        widget=TinyMCEWidget(
            label=_(u"FacultyStaffDirectory_label_overview_text",
                    default=u"Overview text (used for specialty overview view)"),
            i18n_domain='FacultyStaffDirectory',
        ),
        default_output_type="text/x-html-safe",
        searchable=True,
        validators=('isTidyHtmlWithCleanup',)
    )

),
)

Specialty_schema = getattr(PersonGrouping, 'schema', atapi.Schema(())).copy() + schema.copy()

class Specialty(PersonGrouping):
    """
    """
    security = ClassSecurityInfo()
    implements(ISpecialty)
    meta_type = portal_type = 'FSDSpecialty'

    _at_rename_after_creation = True
    schema = Specialty_schema
    # Methods
    security.declareProtected(View, 'getSpecialtyInformation')
    def getSpecialtyInformation(self, person):
        """
        Get the specialty information for a specific person
        """
        refCatalog = getToolByName(self, 'reference_catalog')
        refs = refCatalog.getReferences(self, 'SpecialtyInformation', person)

        if refs:
            return refs[0].getContentObject()
        else:
            return None

atapi.registerType(Specialty, config.PROJECTNAME)
