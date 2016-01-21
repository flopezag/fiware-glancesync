#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U
#
# This file is part of FI-WARE project.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at:
#
#        http://www.apache.org/licenses/LICENSE-2.0
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

# Import flask dependencies
from flask import Blueprint, Response
import httplib
import datetime
from app.settings.settings import OWNER, VERSION, API_INFO_URL, UPDATED, STATUS, CONTENT_TYPE

__author__ = 'fla'

# Define the blueprint: 'auth', set its url prefix: app.url/regions
mod_info = Blueprint('info', __name__, url_prefix='/')

ID = 'v' + VERSION
RUNNINGFROM = datetime.datetime.now()



# Set the route and accepted methods
@mod_info.route('/', methods=['GET'])
def get_info():
    """
    Lists information about GlanceSync API version.
    :return: JSON responses with the detailed information about the Glancesync API
    """
    message = "{\"id\": \"%s\", \"owner\": \"%s\", \"status\": \"%s\", \"version\": \"%s\", \"updated\": \"%s\", " \
              "\"runningfrom\": \"%s\", \"href\": \"%s\" }\n" \
              % (ID, OWNER, STATUS, VERSION, UPDATED, RUNNINGFROM, API_INFO_URL)

    return Response(response=message,
                    status=httplib.OK,
                    content_type=CONTENT_TYPE)
