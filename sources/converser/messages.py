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


''' Concrete message and content implementations. '''


from . import __
from . import canisters as _canisters


class Message( __.immut.DataclassObject ):
    ''' Base class for message implementations. '''

    role: _canisters.Role
    timestamp: __.datetime.datetime


class UserMessage( Message ):
    ''' User message implementation. '''

    role: _canisters.Role
    timestamp: __.datetime.datetime
    content: tuple[ _canisters.Content, ... ]

    @classmethod
    def produce(
        cls,
        content: __.cabc.Sequence[ _canisters.Content ],
        timestamp: __.Absential[ __.datetime.datetime ] = __.absent,
    ) -> __.typx.Self:
        ''' Produces user message with defaults. '''
        if __.is_absent( timestamp ):
            timestamp = __.datetime.datetime.now( __.datetime.timezone.utc )
        return cls(
            role = _canisters.Role.User,
            timestamp = timestamp,
            content = tuple( content ),
        )


class AssistantMessage( Message ):
    ''' Assistant message implementation. '''

    role: _canisters.Role
    timestamp: __.datetime.datetime
    content: __.Absential[ tuple[ _canisters.Content, ... ] ]

    @classmethod
    def produce(
        cls,
        content: __.Absential[
            __.cabc.Sequence[ _canisters.Content ]
        ] = __.absent,
        timestamp: __.Absential[ __.datetime.datetime ] = __.absent,
    ) -> __.typx.Self:
        ''' Produces assistant message with defaults. '''
        if __.is_absent( timestamp ):
            timestamp = __.datetime.datetime.now( __.datetime.timezone.utc )
        content_tuple = (
            tuple( content ) if not __.is_absent( content ) else __.absent
        )
        return cls(
            role = _canisters.Role.Assistant,
            timestamp = timestamp,
            content = content_tuple,
        )


class SupervisorMessage( Message ):
    ''' Supervisor message implementation. '''

    role: _canisters.Role
    timestamp: __.datetime.datetime
    content: tuple[ _canisters.Content, ... ]
    cache_control: __.Absential[ __.immut.Dictionary[ str, __.typx.Any ] ]

    @classmethod
    def produce(
        cls,
        content: __.cabc.Sequence[ _canisters.Content ],
        cache_control: __.Absential[
            __.cabc.Mapping[ str, __.typx.Any ]
        ] = __.absent,
        timestamp: __.Absential[ __.datetime.datetime ] = __.absent,
    ) -> __.typx.Self:
        ''' Produces supervisor message with defaults. '''
        if __.is_absent( timestamp ):
            timestamp = __.datetime.datetime.now( __.datetime.timezone.utc )
        cache_dict = (
            __.immut.Dictionary( cache_control )
            if not __.is_absent( cache_control )
            else __.absent
        )
        return cls(
            role = _canisters.Role.Supervisor,
            timestamp = timestamp,
            content = tuple( content ),
            cache_control = cache_dict,
        )


class DocumentMessage( Message ):
    ''' Document message implementation. '''

    role: _canisters.Role
    timestamp: __.datetime.datetime
    content: tuple[ _canisters.Content, ... ]
    document_id: str

    @classmethod
    def produce(
        cls,
        document_id: str,
        content: __.cabc.Sequence[ _canisters.Content ],
        timestamp: __.Absential[ __.datetime.datetime ] = __.absent,
    ) -> __.typx.Self:
        ''' Produces document message with defaults. '''
        if __.is_absent( timestamp ):
            timestamp = __.datetime.datetime.now( __.datetime.timezone.utc )
        return cls(
            role = _canisters.Role.Document,
            timestamp = timestamp,
            content = tuple( content ),
            document_id = document_id,
        )


class InvocationMessage( Message ):
    ''' Invocation message implementation. '''

    role: _canisters.Role
    timestamp: __.datetime.datetime
    invocation_id: str
    name: str
    arguments: __.immut.Dictionary[ str, __.typx.Any ]

    @classmethod
    def produce(
        cls,
        invocation_id: str,
        name: str,
        arguments: __.cabc.Mapping[ str, __.typx.Any ],
        timestamp: __.Absential[ __.datetime.datetime ] = __.absent,
    ) -> __.typx.Self:
        ''' Produces invocation message with defaults. '''
        if __.is_absent( timestamp ):
            timestamp = __.datetime.datetime.now( __.datetime.timezone.utc )
        return cls(
            role = _canisters.Role.Invocation,
            timestamp = timestamp,
            invocation_id = invocation_id,
            name = name,
            arguments = __.immut.Dictionary( arguments ),
        )


class ResultMessage( Message ):
    ''' Result message implementation. '''

    role: _canisters.Role
    timestamp: __.datetime.datetime
    invocation_id: str
    content: tuple[ _canisters.Content, ... ]
    error: __.Absential[ str ]

    @classmethod
    def produce(
        cls,
        invocation_id: str,
        content: __.cabc.Sequence[ _canisters.Content ],
        error: __.Absential[ str ] = __.absent,
        timestamp: __.Absential[ __.datetime.datetime ] = __.absent,
    ) -> __.typx.Self:
        ''' Produces result message with defaults. '''
        if __.is_absent( timestamp ):
            timestamp = __.datetime.datetime.now( __.datetime.timezone.utc )
        return cls(
            role = _canisters.Role.Result,
            timestamp = timestamp,
            invocation_id = invocation_id,
            content = tuple( content ),
            error = error,
        )
