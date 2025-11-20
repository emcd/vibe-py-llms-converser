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


''' Conversation lifecycle event protocols. '''


from . import __


class Event( __.immut.DataclassObject ):
    ''' Base class for conversation events. '''

    message_id: str


class MessageAllocationEvent( Event ):
    ''' Message allocation begins. '''

    message_id: str


class MessageProgressEvent( Event ):
    ''' Streaming chunk received. '''

    message_id: str
    chunk: str


class MessageUpdateEvent( Event ):
    ''' Message content updated. '''

    message_id: str


class MessageCompletionEvent( Event ):
    ''' Message finalized successfully. '''

    message_id: str


class MessageAbortEvent( Event ):
    ''' Message generation failed. '''

    message_id: str
    error: str


ConversationEvent: __.typx.TypeAlias = __.typx.Union[
    MessageAllocationEvent,
    MessageProgressEvent,
    MessageUpdateEvent,
    MessageCompletionEvent,
    MessageAbortEvent,
]

EventHandler: __.typx.TypeAlias = __.cabc.Callable[ [ Event ], None ]
