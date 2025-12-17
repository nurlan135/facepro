"""
FacePro Face Enrollment Module
Üz qeydiyyatı və idarəetmə komponentləri.
"""

from .widgets import ClickableImageLabel, FacePreviewWidget, PersonCardWidget
from .enrollment_dialog import FaceEnrollmentDialog
from .manage_dialog import ManageFacesDialog, EditEncodingsDialog

__all__ = [
    'ClickableImageLabel',
    'FacePreviewWidget', 
    'PersonCardWidget',
    'FaceEnrollmentDialog',
    'ManageFacesDialog',
    'EditEncodingsDialog'
]
