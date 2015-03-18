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
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For those usages not covered by the Apache version 2.0 License please
# contact with opensource@tid.es
#
author = 'jmpr22'


class GlanceSyncImage(object):
    """This class represent an image within a regional image server.

    Its representation is independent of the obtained from the glance server

    The raw field is an opaque object for internal use only. It is the original
    object obtained from the server and may vary depending of version or the
    method used to get the object.
    """

    def __init__(self, name, id, region, owner=None, is_public=True,
                 checksum=None, size=0, status=None, user_properties=None,
                 raw=None):
        """Constructor of the image object.

        This constructor is usually not invoked by the user"""
        self.name = name
        self.id = id
        self.region = region
        self.is_public = is_public
        self.checksum = checksum
        self.raw = raw
        self.size = size
        self.status = status
        self.owner = owner
        if user_properties is not None:
            self.user_properties = user_properties
        else:
            self.user_properties = dict()

    def __str__(self):
        """It Returns the string representation of the class"""

        s = 'Region: {0} Name: {1} Id: {2} Status: {3} Size: {4} ' +\
            'Checksum: {5} Owner {6} Public: {7} Properties: {8}'
        return s.format(
            self.region, self.name, self.id, self.status, self.size,
            self.checksum, self.owner, self.is_public,
            str(self.user_properties))

    def to_field_list(self, user_properties_list=None):
        """It returns a list with the fields of the class.

        The last field if the string representation of the dictionary
        user_properties, unless user_properties_list is provided. If provided,
        each specified user property is append to the list.

        This method is useful in combination with a csv writer.
        """
        output = [self.region, self.name, self.id, self.status, self.size,
                  self.checksum, self.owner, self.is_public]
        if user_properties_list:
            for field in user_properties_list:
                if field in self.user_properties:
                    output.append(self.user_properties[field])
                else:
                    output.append('')
        else:
            output.append(str(self.user_properties))
        return output

    def csv_userproperties(self, fields):
        """Extract the fields of the image as a CSV

        Only the image name and the user properties specified in the
        field list are listed.
        """
        sub = list()
        sub.append(self.name)
        for field in fields:
            if field in self.user_properties:
                sub.append(self.user_properties[field])
            else:
                sub.append('')
        return ','.join(sub)

    def compare_with_masterregion(self, master_region_images,
                                  user_properties=None):
        """
        It compares this image with its homonyms on master region and
        returns a character identifying the image synchronization status.

        It detects anomalies: the image is present but with different metadata
        or checksum, or the image it is not ready. It also detect when the
        image is not on master region or it is public here but private on
        master region. This last information is only for reporting, because the
        synchronisation way is always from master region to the other regions.

        :param master_region_images: a dictionary with the master region's
         images.
        :param user_properties: a list with the user properties to compare;
           other properties are considered local. If None, all metadata is
           compared.
        :return: It returns an empty string when the image is synchronized.
        In other way:
        +: this image is not on the master glance server
        $: this image is not active: may be still uploading or in an error
           status.
        -: this image is on the master glance server, but as non-public
        _: this image is on the master glance server, but there is public and
           here it is not.
        !: this image is on the master glance server, but checksum is different
        #: this image is on the master glance server, but some of the
           user properties are different
        """

        if self.name not in master_region_images:
            return '+'

        if self.status != 'active':
            return '$'

        image_master = master_region_images[self.name]
        if image_master.checksum != self.checksum:
            return '!'

        if image_master.is_public != self.is_public:
            if image_master.is_public == 'No':
                return '-'
            else:
                return '_'

        if user_properties and len(user_properties) > 0:
            for prop in user_properties:
                # This is a special case: values usually are different
                if prop == 'kernel_id' or prop == 'ramdisk_id':
                    continue
                val_m = image_master.user_properties.get(prop, None)
                val_l = self.user_properties.get(prop, None)

                if val_m != val_l:
                    return '#'
        else:
            if len(self.user_properties) != len(image_master.user_properties):
                return '#'
            for prop in self.user_properties:
                # This is a special case: values usually are different
                if prop == 'kernel_id' or prop == 'ramdisk_id':
                    continue
                val_m = image_master.user_properties.get(prop, None)
                val_l = self.user_properties.get(prop, None)

                if val_m != val_l:
                    return '#'

        return ''

    def is_synchronisable(
            self, metadata_set, forcesync, metadata_condition=None):
        """Determines if the image is synchronisable according to this
        algorith:
           if image id is in forcesync list, it is synchronisable
           if metadata_condition is provided, evaluate it and return the result
           if image is not public, it is not synchronisable
           if metadata_set is empty, it is synchronisable

        :param metadata_set: list of user properties to consider
        :param forcesync: a list with UUID of images that are always sync.
        :param metadata_condition: expresion to evaluate if the image is sync.
        :return:
        """
        if self.id in forcesync:
            return True

        if metadata_condition:
            image = self
            globals_dict = dict()
            globals_dict['image'] = self
            globals_dict['metadata_set'] = metadata_set
            return eval(metadata_condition, globals_dict)

        if self.is_public == 'No':
            return False

        if not metadata_set:
            return True

        some_property_in = False
        for prop in metadata_set:
            if prop in self.user_properties:
                some_property_in = True
                break
        return some_property_in
