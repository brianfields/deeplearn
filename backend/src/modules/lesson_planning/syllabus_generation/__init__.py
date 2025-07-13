"""
Syllabus Generation Submodule

This submodule handles the generation of learning syllabi.
"""

from .service import SyllabusGenerationService
from .prompts import SyllabusGenerationPrompt

__all__ = ['SyllabusGenerationService', 'SyllabusGenerationPrompt']