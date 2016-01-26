#!/usr/bin/env python
# -- encoding: utf-8 --
#
# Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U
#
# This file is part of FI-Core project.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For those usages not covered by the Apache version 2.0 License please
# contact with opensource@tid.es
#
# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from app import db
from utils.mydict import FirstInsertFirstOrderedDict as fifo
import uuid

__author__ = 'fla'


# Define a base model for other database tables to inherit
class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime,  default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime,  default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


# Define a User model
class User(Base):
    __tablename__ = 'auth_user'

    # User name: Identification data
    name = db.Column(db.String(128), nullable=False, unique=True)

    # Authorisation Data: role
    role = db.Column(db.String(128), nullable=False)

    # Status of synchronisation operation
    status = db.Column(db.String(128), nullable=False)

    # New instance instantiation procedure
    def __init__(self, name, role, status):
        self.name = name
        self.role = role
        self.status = status

    def __repr__(self):
        return '<User %r>' % self.name


class TokenModel:
    """
    Define a Token model (in current version not stored in DB.
    """
    tenant = None
    id = None
    expires = None

    def __init__(self, tenant, id, expires):
        self.tenant = tenant
        self.id = id
        self.expires = expires


class Image:
    """
    Define a Image model to be used in the response of the GlaceSync API.
    id: Image id corresponding to the Glance service in a region (e.g. "3cfeaf3f0103b9637bb3fcfe691fce1e").
    name: Name of the image in the master (Spain2) node (e.g. "base_ubuntu_14.04").
    status: Status of the synchronization of the images
       (see https://github.com/telefonicaid/fiware-glancesync#checking-status for more information).
    message = Error message of the synchronization or null if all was ok.
    glancestatus = GlanceSync synchronization status
    """

    id = None       # Ex id = "3cfeaf3f0103b9637bb3fcfe691fce1e",
    name = None     # Ex name = "base_ubuntu_14.04",
    status = None   # Ex status = "ok",
    message = None  # Ex message = null,

    # Constants associated to the glancesync status
    OK = 'ok'
    OK_STALLED_CHECKSUM = 'ok_stalled_checksum'
    ERROR_CHECKSUM = 'error_checksum'
    ERROR_AMI = 'error_ami'
    PENDING_METADATA = 'pending_metadata'
    PENDING_UPLOAD = 'pending_upload'
    PENDING_REPLACE = 'pending_replace'
    PENDING_RENAME = 'pending_rename'
    PENDING_AMI = 'pending_ami'

    # GlanceSync synchronization status
    glancestatus = {'ok', 'ok_stalled_checksum',
                    'error_checksum', 'error_ami',
                    'pending_metadata', 'pending_upload', 'pending_replace', 'pending_rename', 'pending_ami'}

    def __init__(self, identify, name, status, message):
        """
        Default constructor of the class.
        :param identify: Id of the image.
        :param name: Name of the image.
        :param status: Status of the synchronization process.
        :param message: Message about the proccess if something was wrong.
        :return:
        """
        self.id = identify
        self.name = name
        self.status = status
        self.message = message

        try:
            self.check_status()
        except ValueError as ex:
            raise ex

    def check_status(self):
        if self.status not in self.glancestatus:
            raise ValueError('Error, the status does not correspond to any of the defined values',
                             self.status, self.glancestatus)

        return True

    def dump(self):
        expectedkey = ['id', 'name', 'status', 'message']
        expectedvalue = [self.id, self.name, self.status, self.message]

        my_dict = fifo(expectedkey, expectedvalue)

        return my_dict.dump()


class Images:
    """
    Define a list of images to be manage by the glancesync tool. Basically it is a list of Image
    """
    def __init__(self):
        """
        Constructor of the class Images
        :param number_of_images: Number of Images to manage in the array
        """
        self.number_of_images = 0
        self.images = []

    def add(self, data):
        """
        Add a new Image to the array.
        :param data: Data array to use in the constructor of the Image.
        """
        if len(data) != 4:
            raise ValueError("Error, data should be a array with len equal to 4")
        elif isinstance(data, list):
            tmp = Image(identify=data[0],
                        name=data[1],
                        status=data[2],
                        message=data[3])

            self.images.append(tmp)

            self.number_of_images = self.number_of_images + 1

    def dump(self):
        """
        Generate json message with the content of the Images
        :return: json message
        """
        result = self.images[0].dump().replace('\"', '\'')

        if self.number_of_images > 1:
            for i in range(1, self.number_of_images):
                result = result + ', ' + self.images[1].dump().replace('\"', '\'')

        result = '{images: [' + result + ']}'

        return result


class Task:
    def __init__(self, status=None):
        self.taskid = uuid.uuid1()

        if status is not None:
            if status not in ('synced', 'syncing', 'failed'):
                raise ValueError("Status message should be synced, syncing or failed")
            else:
                self.status = status
        else:
            self.status = status

    def dump(self):
        if self.status is None:
            result = "{'taskId': '" + str(self.taskid) + "'}"
        else:
            result = "{'taskId': '" + str(self.taskid) + "', 'status': '" + self.status + "'}"

        return result
