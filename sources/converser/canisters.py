# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.          #
#  You may obtain a copy of the License at                                   #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  Unless required by applicable law or agreed to in writing, software       #
#  distributed under the License is distributed on an "AS IS" BASIS,         #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' Message abstraction protocols and implementations. '''


from . import __


class Content( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' Base protocol for message content. '''

    mime_type: str


class Role( __.enum.Enum ):
    '''
    Platform-neutral message role enumeration.

    Implementations must map these roles to their native roles or constructs
    as appropriate. Each role corresponds to a specific canister type.
    '''

    User = 'user'
    Assistant = 'assistant'
    Supervisor = 'supervisor'
    Document = 'document'
    Invocation = 'invocation'
    Result = 'result'


class Canister( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' Base protocol for conversation messages. '''

    role: Role
    timestamp: __.datetime.datetime


class UserCanister( Canister ):
    ''' User input message. '''

    content: __.cabc.Sequence[ Content ]


class AssistantCanister( Canister ):
    ''' Assistant response message. '''

    content: __.Absential[ __.cabc.Sequence[ Content ] ]


class SupervisorCanister( Canister ):
    ''' System instruction message. '''

    content: __.cabc.Sequence[ Content ]
    cache_control: __.Absential[ __.cabc.Mapping[ str, __.typx.Any ] ]


class DocumentCanister( Canister ):
    ''' Reference document message. '''

    content: __.cabc.Sequence[ Content ]
    document_id: str


class InvocationCanister( Canister ):
    ''' Tool invocation request message. '''

    invocation_id: str
    name: str
    arguments: __.immut.Dictionary[ str, __.typx.Any ]


class ResultCanister( Canister ):
    ''' Tool execution result message. '''

    invocation_id: str
    content: __.cabc.Sequence[ Content ]
    error: __.Absential[ str ]


class TextContent( Content ):
    ''' Textual content implementation. '''

    text: str
    mime_type: str = 'text/plain'


class PictureContent( Content ):
    ''' Picture content implementation. '''

    content_id: str
    mime_type: str
    source_location: __.Absential[ str ] = __.absent
