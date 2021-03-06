# -*- coding: utf-8 -*-

# Copyright 2015-2016 Telefónica Investigación y Desarrollo, S.A.U
#
# This file is part of FIWARE project.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For those usages not covered by the Apache version 2.0 License please
# contact with opensource@tid.es


from constants import KEYSTONE_GLANCE_SERVICE_NAME, IMAGES_DIR
from qautils.logger.logger_utils import get_logger
import shutil
from glanceclient.client import Client as GlanceClient
from keystoneclient.v2_0.client import Client as KeystoneClient
import os

__copyright__ = "Copyright 2015-2016"
__license__ = " Apache License, Version 2.0"

__logger__ = get_logger("qautils")


class GlanceOperations():

    def __init__(self, auth_username, auth_password, auth_tenant_id, auth_url, region_name):
        """
        Init GlanceClient using the given credentials.
        :param username (string): Keystone Username
        :param password (string): Password
        :param tenant_id (string): Tenant ID
        :param auth_url (string): Auth URL
        :param region_name: Region name
        :return:
        """

        # Initialize session trying to get auth token; on success, continue with initialization
        self.auth_token = self.__init_auth__(auth_username, auth_password, auth_tenant_id, auth_url)
        self.region_name = region_name
        self.tenant_id = auth_tenant_id
        if self.auth_token:

            # Load Glance URL (public) from Keystone
            glance_public_url = self.__get_glance_endpoint_from_keystone__(region_name)

            __logger__.info("Glance public URL: %s", glance_public_url)
            self.glance_client = GlanceClient(endpoint=glance_public_url, version='1', token=self.auth_token)

    def __get_resource_path__(self, image_filename):
        current = os.getcwd()

        if "tests/acceptance" in current:
            image_path = "{}/{}".format(IMAGES_DIR, image_filename)
        else:
            image_path = "tests/acceptance/{}/{}".format(IMAGES_DIR, image_filename)

        return image_path

    def __get_glance_endpoint_from_keystone__(self, region_name):
        """
        Get the endpoint of Glance from Keystone Service Catalog
        :param region_name: Name of the region
        :return:
        """

        for service in self.keystone_client.auth_ref['serviceCatalog']:
            if service['name'] == KEYSTONE_GLANCE_SERVICE_NAME:
                for endpoint in service['endpoints']:
                    if endpoint['region'] == region_name:
                        endpoint = endpoint["publicURL"]
                        break
                break
        __logger__.debug("Glance endpoint (Service: %s, Type: 'publicURL', Region: %s) is: %s",
                         KEYSTONE_GLANCE_SERVICE_NAME, region_name, endpoint)
        return endpoint

    def __init_auth__(self, username, password, tenant_id, auth_url):
        """
        Init the variables related to authorization, needed to execute tests.
        :param username (string): Keystone Username
        :param password (string): Password
        :param tenant_id (string): Tenant ID
        :param auth_url (string): Auth URL
        :return: The auth token retrieved
        """

        __logger__.debug("Init auth")
        self.keystone_client = \
            KeystoneClient(username=username,
                           password=password,
                           tenant_id=tenant_id,
                           auth_url=auth_url)

        if self.keystone_client is None:
            __logger__.debug("Authentication error.")
            return None
        else:
            token = self.keystone_client.auth_ref['token']['id']
            __logger__.debug("Auth token: '%s'", token)
            return token

    def create_image(self, image_glance_name, image_filename=None, container_format="bare", disk_format="qcow2",
                     custom_properties=dict(), is_public=True):
        """
        Create a new image in the configured Glance with the given parameters
        :param image_glance_name (string): Name of the image.
        :param image_filename (string): Name of the resource file to use as "image".
                If None, no image will be uploaded and status will not be ACTIVE
        :param container_format (string): Container format (Glance). Default: 'bare'
        :param disk_format (string): Disk format (Glance). Default: 'qcow2'
        :param custom_properties (dict): User properties to be added in the image metadata
        :return (string): Image id.
        """

        __logger__.debug("Creating new image '%s' in '%s' with the tenant '%s'", image_glance_name, self.region_name,
                         self.tenant_id)
        image = self.glance_client.images.create(name=image_glance_name,
                                                 container_format=container_format, disk_format=disk_format)
        __logger__.debug("Image created: %s", str(image))

        if image_filename:
            image_path = self.__get_resource_path__(image_filename)
            __logger__.debug("Updating image with content from file '%s'", image_path)
            image.update(data=open(image_path, 'rb'))

            glance_file_name = "/var/lib/glance/images/" + image.id

            if os.path.exists(("/var/lib/glance/images")):
                __logger__.debug("Storing image with content from file '%s'", glance_file_name)
                shutil.copy(image_path, glance_file_name)

        __logger__.debug("Updating image property: 'is_public=%s'", is_public)
        image.update(properties=custom_properties, is_public=is_public)

        if custom_properties:
            __logger__.debug("Updating image with custom properties: '%s'", custom_properties)
            image.update(properties=custom_properties)
        return image.id

    def update_image_properties(self, image_id, **kwargs):
        """
        Update the image properties of the given image_id
        :param image_id: Image ID
        :param **kwargs: Optional params:
            - custom_properties (dict): User properties to be added in the image metadata
            - name (string): Image name to be updated.
            - is_public (boolean): Visibility of the image.
        :return: None
        """

        if "custom_properties" in kwargs:
            __logger__.debug("Updating image with custom properties: '%s'", kwargs["custom_properties"])
            self.glance_client.images.update(image_id, properties=kwargs["custom_properties"])

        if "name" in kwargs:
            __logger__.debug("Updating image name to '%s'", kwargs['name'])
            self.glance_client.images.update(image_id, name=kwargs['name'])

        if "is_public" in kwargs:
            __logger__.debug("Updating visibility of the image to '%s'", kwargs['is_public'])
            self.glance_client.images.update(image_id, is_public=kwargs['is_public'])

    def update_image_properties_by_name(self, image_name, **kwargs):
        """
        Update properties of all images found by the given name
        :param image_name: Name of the image to update (data)
        :param **kwargs: Optional params:
            - custom_properties (dict): User properties to be added in the image metadata
            - name (string): New image name to be updated.
            - is_public (boolean): Visibility of the image.
        :return: None
        """

        __logger__.debug("Updating all images by name '%s'. Props: '%s'", image_name, kwargs)
        for image in self.get_images(image_name):
            self.update_image_properties(image.id, **kwargs)

    def remove_image(self, image_id):
        """
        Remove the given image id from Glance
        :param image_id (string): Image ID.
        :return: None
        """

        __logger__.debug("Deleting image '%s' from '%s'", image_id, self.region_name)
        self.glance_client.images.delete(image_id)

    def remove_all_images_by_name(self, image_name):
        """
        Remove all images that match with the given image name.
        :param image_name (string): Name of the image.
        :return: None
        """

        __logger__.debug("Deleting all images by name '%s'", image_name)
        for image in self.get_images(image_name):
            self.remove_image(image.id)

    def get_images(self, image_name):
        """
        Get all images that match with the given image name.
        :param image_name (string): Name of the image.
        :return (list): List of images
        """

        __logger__.debug("Getting image '%s' from '%s'", image_name, self.region_name)
        return list(self.glance_client.images.list(filters={"name": image_name}))

    def get_data_as_string(self, image_id):
        """
        Get raw content of the image as string.
        :param image_id (sting): ID of the image.
        :return (string): Image RAW content
        """

        __logger__.debug("Getting data from image '%s'", image_id)
        image_data = self.glance_client.images.data(image_id, do_checksum=True)
        raw_data = ""
        for chunk in image_data:
            raw_data += str(chunk)
        return raw_data
