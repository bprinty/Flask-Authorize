
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship, backref

from sqlalchemy.ext.declarative import declared_attr

from flask_authorize.mixins import PipedList

def generate_association_table(entity_name, resource_name, entity_tablename=None, resource_tablename=None):

    # Make them plural by adding 's' :)
    if not entity_tablename:
        entity_tablename = entity_name.lower() + 's'
    if not resource_tablename:
        resource_tablename = resource_name.lower() + 's'

    # More names
    entity_name_lower = entity_name.lower()
    resource_name_lower = resource_name.lower()

    @declared_attr
    def left_id(cls):
        return Column(Integer, ForeignKey(f"{entity_tablename}.id"), primary_key=True)
    
    @declared_attr
    def right_id(cls):
        return Column(Integer, ForeignKey(f"{resource_tablename}.id"), primary_key=True)
    
    @declared_attr
    def entity_relationship(cls):
        return relationship(f"{entity_name}", backref=backref(f"special_{resource_tablename}", lazy="dynamic"))
    
    @declared_attr
    def resource_relationship(cls):
        return relationship(f"{resource_name}", backref=backref(f"special_{entity_tablename}", lazy="dynamic"))

    class PermissionsAssociationMixin:
        __tablename__ = f"{entity_tablename}_{resource_tablename}_association"

        entity_id = left_id
        resource_id = right_id

        locals()[f"special_{entity_tablename}"] = entity_relationship
        locals()[f"special_{resource_tablename}"] = resource_relationship

        permissions = Column(PipedList)

    return PermissionsAssociationMixin
        
    