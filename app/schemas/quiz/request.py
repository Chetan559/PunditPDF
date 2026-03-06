from pydantic import BaseModel, Field
from enum import Enum


class QuestionType(str, Enum):
    MCQ               = "mcq"
    TRUE_FALSE        = "true_false"
    FILL_IN_THE_BLANK = "fill_in_the_blank"


class DifficultyLevel(str, Enum):
    EASY   = "easy"
    MEDIUM = "medium"
    HARD   = "hard"


class QuizGenerateRequest(BaseModel):
    count:         int             = Field(default=5, ge=3, le=20)
    question_type: QuestionType    = Field(default=QuestionType.MCQ)
    difficulty:    DifficultyLevel = Field(default=DifficultyLevel.MEDIUM)
    topic:         str | None      = Field(default=None)
    user_id:       str             = "default_user"


class QuizAppendRequest(BaseModel):
    count:         int                    = Field(default=5, ge=1, le=20)
    question_type: QuestionType | None    = None
    difficulty:    DifficultyLevel | None = None


class QuizSubmitRequest(BaseModel):
    answers: dict[str, str] = Field(description="{question_id: user_answer}")