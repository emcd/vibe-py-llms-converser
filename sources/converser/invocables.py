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


''' Tool calling framework protocols and implementations. '''


from . import __


Context: __.typx.TypeAlias = __.cabc.Mapping[ str, __.typx.Any ]

Invocable: __.typx.TypeAlias = __.cabc.Callable[
    [ Context, __.immut.Dictionary[ str, __.typx.Any ] ],
    __.cabc.Awaitable[ __.typx.Any ],
]


class Invoker( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' Tool wrapper with metadata and validation. '''

    name: str
    invocable: Invocable
    arguments_schema: __.immut.Dictionary[ str, __.typx.Any ]
    ensemble: 'Ensemble'

    @__.abc.abstractmethod
    async def __call__(
        self,
        context: Context,
        arguments: __.immut.Dictionary[ str, __.typx.Any ],
    ) -> __.typx.Any:
        raise NotImplementedError


class Ensemble( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' Grouped invokers with lifecycle management. '''

    name: str
    invokers: __.immut.Dictionary[ str, Invoker ]
    configuration: __.immut.Dictionary[ str, __.typx.Any ]
    connection: __.Absential[ __.typx.Any ]

    @__.abc.abstractmethod
    async def connect( self ) -> None:
        raise NotImplementedError

    @__.abc.abstractmethod
    async def disconnect( self ) -> None:
        raise NotImplementedError


class InvokerRegistry( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' Registry for all available invokers. '''

    @__.abc.abstractmethod
    def register_ensemble( self, ensemble: Ensemble ) -> None:
        raise NotImplementedError

    @__.abc.abstractmethod
    def access_invoker( self, name: str ) -> __.Absential[ Invoker ]:
        raise NotImplementedError

    @__.abc.abstractmethod
    def survey_ensembles( self ) -> __.cabc.Sequence[ Ensemble ]:
        raise NotImplementedError

    @__.abc.abstractmethod
    def survey_invokers( self ) -> __.cabc.Sequence[ Invoker ]:
        raise NotImplementedError
