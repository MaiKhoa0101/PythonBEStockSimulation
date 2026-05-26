from sqlalchemy import inspect as sa_inspect
from dataclasses import asdict


from sqlalchemy import inspect as sa_inspect
from dataclasses import asdict


def dto_to_entity(dto, entity_class, exclude: set = None, overrides: dict = None):
    exclude = exclude or set()
    overrides = overrides or {}
    valid_fields = set(entity_class.__dataclass_fields__)
    dto_dict = dto.model_dump() if hasattr(dto, "model_dump") else dto.dict()
    filtered = {k: v for k, v in dto_dict.items() if k in valid_fields and k not in exclude}
    filtered.update(overrides)
    return entity_class(**filtered)


def entity_to_model(entity, model_class, exclude: set = None):
    exclude = exclude or set()
    valid_columns = {col.key for col in sa_inspect(model_class).mapper.column_attrs}
    entity_dict = asdict(entity)
    filtered = {k: v for k, v in entity_dict.items() if k in valid_columns and k not in exclude}
    return model_class(**filtered)


def update_model_from_entity(entity, model_instance, exclude: set = None):
    exclude = exclude or set()
    valid_columns = {col.key for col in sa_inspect(model_instance.__class__).mapper.column_attrs}
    for k, v in asdict(entity).items():
        if k in valid_columns and k not in exclude:
            setattr(model_instance, k, v)
    return model_instance


def model_to_entity(model_instance, entity_class, overrides: dict = None):
    overrides = overrides or {}
    valid_fields = set(entity_class.__dataclass_fields__)
    data = {col: getattr(model_instance, col) for col in valid_fields if hasattr(model_instance, col)}
    data.update(overrides)
    return entity_class(**data)


def entity_to_dto(entity, dto_class, exclude: set = None, overrides: dict = None):
    if not entity:
        return None
        
    exclude = exclude or set()
    overrides = overrides or {}
    valid_fields = (
        set(dto_class.model_fields)
        if hasattr(dto_class, "model_fields")
        else set(dto_class.__fields__)
    )
    entity_dict = asdict(entity)
    filtered = {k: v for k, v in entity_dict.items() if k in valid_fields and k not in exclude}
    filtered.update(overrides)
    return dto_class(**filtered)