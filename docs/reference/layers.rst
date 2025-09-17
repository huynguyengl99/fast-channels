Channel Layers
==============

.. module:: fast_channels.layers

Channel layer system for enabling communication between different parts of your application.

Registry Functions
------------------

.. autofunction:: fast_channels.layers.get_channel_layer

.. autofunction:: fast_channels.layers.register_channel_layer

.. autofunction:: fast_channels.layers.unregister_channel_layer

Registry Class
--------------

.. autoclass:: fast_channels.layers.ChannelLayerRegistry
   :members:
   :undoc-members:
   :show-inheritance:

Base Channel Layer
------------------

.. autoclass:: fast_channels.layers.BaseChannelLayer
   :members:
   :undoc-members:
   :show-inheritance:

In-Memory Channel Layer
-----------------------

.. autoclass:: fast_channels.layers.InMemoryChannelLayer
   :members:
   :undoc-members:
   :show-inheritance:

Redis Channel Layers
---------------------

.. module:: fast_channels.layers.redis

.. autoclass:: fast_channels.layers.redis.RedisChannelLayer
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_channels.layers.redis.RedisPubSubChannelLayer
   :members:
   :undoc-members:
   :show-inheritance:
