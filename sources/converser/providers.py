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


''' Provider abstraction protocols for LLM access. '''


from . import __
from . import canisters as _canisters
from . import events as _events


Controls: __.typx.TypeAlias = __.cabc.Mapping[ str, __.typx.Any ]


class ModelDescriptor( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' Model metadata and capabilities. '''

    identifier: str
    name: str
    supports_streaming: bool
    supports_tool_calling: bool
    context_window_size: int


class Model( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' LLM model instance with conversation capability. '''

    identifier: str
    descriptor: ModelDescriptor

    @__.abc.abstractmethod
    async def converse(
        self,
        canisters: __.cabc.Sequence[ _canisters.Canister ],
        controls: __.Absential[ Controls ] = __.absent,
        event_handler: __.Absential[ _events.EventHandler ] = __.absent,
    ) -> __.cabc.Sequence[ _canisters.Canister ]:
        raise NotImplementedError


class Client( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' Provider client for model access. '''

    provider_name: str

    @__.abc.abstractmethod
    def access_model( self, identifier: str ) -> Model:
        raise NotImplementedError

    @__.abc.abstractmethod
    def survey_models( self ) -> __.cabc.Sequence[ ModelDescriptor ]:
        raise NotImplementedError


class Provider( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' LLM provider abstraction. '''

    name: str

    @__.abc.abstractmethod
    def produce_client(
        self,
        configuration: __.cabc.Mapping[ str, __.typx.Any ],
    ) -> Client:
        raise NotImplementedError


class MessagesProcessor( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' Bidirectional message format conversion. '''

    @__.abc.abstractmethod
    def normalize_messages(
        self,
        native_messages: __.cabc.Sequence[
            __.cabc.Mapping[ str, __.typx.Any ]
        ],
    ) -> __.cabc.Sequence[ _canisters.Canister ]:
        raise NotImplementedError

    @__.abc.abstractmethod
    def nativize_messages(
        self,
        canisters: __.cabc.Sequence[ _canisters.Canister ],
    ) -> __.cabc.Sequence[ __.immut.Dictionary[ str, __.typx.Any ] ]:
        raise NotImplementedError


class ControlsProcessor( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' Model parameter normalization. '''

    @__.abc.abstractmethod
    def normalize_controls(
        self,
        native_controls: __.cabc.Mapping[ str, __.typx.Any ],
    ) -> Controls:
        raise NotImplementedError

    @__.abc.abstractmethod
    def nativize_controls(
        self,
        controls: Controls,
    ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        raise NotImplementedError


class InvocationsProcessor( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' Tool calling format conversion. '''

    @__.abc.abstractmethod
    def normalize_tools(
        self,
        native_tools: __.cabc.Sequence[ __.cabc.Mapping[ str, __.typx.Any ] ],
    ) -> __.cabc.Sequence[ __.immut.Dictionary[ str, __.typx.Any ] ]:
        raise NotImplementedError

    @__.abc.abstractmethod
    def nativize_tools(
        self,
        tool_schemas: __.cabc.Sequence[ __.cabc.Mapping[ str, __.typx.Any ] ],
    ) -> __.cabc.Sequence[ __.immut.Dictionary[ str, __.typx.Any ] ]:
        raise NotImplementedError


class ConversationTokenizer( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' Token counting for cost tracking. '''

    @__.abc.abstractmethod
    def count_tokens(
        self,
        canisters: __.cabc.Sequence[ _canisters.Canister ],
    ) -> int:
        raise NotImplementedError
