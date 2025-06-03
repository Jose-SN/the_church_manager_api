from bson import ObjectId
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: any,
        handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.plain_validator_function_schema(cls.validate),
            ]),
            serialization=core_schema.plain_serializer_function_schema(str)
        )

    @classmethod
    def validate(cls, v, handler=None): # handler is for compatibility, not always used
        if isinstance(v, ObjectId):
            return v
        if ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    def __repr__(self):
        return f'PyObjectId({super().__repr__()})'
