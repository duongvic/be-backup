from benji import errors
from benji.database import Node, Storage
from benji.services import base
from benji.services.node.model import NodeModel


class NodeController(base.BaseService):
    def __init__(self, config):
        super(NodeController, self).__init__(config)

    def get_node(self, ctx):
        if not ctx.is_admin():
            ctx.set_error(error=errors.USER_ACTION_NOT_ALLOWED, status=403)
            return

        with NodeModel(self._config) as model:
            node = model.get(ctx.data['id'])
            if node is None:
                ctx.set_error("Not found item", status=404)
                return

            ctx.response = node.to_dict()

    def list_nodes(self, ctx):
        res = []
        condition = None
        if not ctx.is_admin():
            ctx.set_error(error=errors.USER_ACTION_NOT_ALLOWED, status=403)
            return

        with NodeModel(self._config) as model:
            nodes, objects, prev_page = model.dump_raw_object(ctx, Node, condition)
            storage_count = 0
            for node in nodes:
                storage = Storage.raw_query().filter(Storage.node_id == node.id).all()
                storage_count += len(storage)
                node_dict = node.to_dict()
                node_dict.update(storage_count=storage_count)
                res.append(dict(node_dict))

            response = {
                'data': res,
                'has_more': objects.has_next,
                'next_page': objects.next_num if objects.has_next else None,
                'prev_page': prev_page,
            }
            ctx.response = response

    def create_node(self, ctx):
        if not ctx.is_admin():
            ctx.set_error(error=errors.USER_ACTION_NOT_ALLOWED, status=403)
            return

        with NodeModel(self._config) as model:
            data = ctx.data
            obj, err = model.create(**data)
            if err:
                ctx.set_error('Failed to create node', status=400)
                return

            ctx.response = obj.to_dict()
            ctx.status = 201

    def update_node(self, ctx):
        data = ctx.data
        if not ctx.is_admin():
            ctx.set_error(error=errors.USER_ACTION_NOT_ALLOWED, status=403)
            return

        with NodeModel(self._config) as model:
            node = model.get(data.pop('id', None))
            if model is None:
                ctx.set_error("Not found item", status=404)
                return

            obj, err = model.update(node.id, **ctx.data)
            if err:
                ctx.set_error('Failed to update node', status=400)
                return

            ctx.response = obj.to_dict()

    def delete_node(self, ctx):
        data = ctx.data
        if not ctx.is_admin():
            ctx.set_error(error=errors.USER_ACTION_NOT_ALLOWED, status=403)
            return

        with NodeModel(self._config) as model:
            node = model.get(data.pop('id', None))
            if model is None:
                ctx.set_error("Not found item", status=400)
                return

            obj, err = model.delete(node.id, data['force'])
            if err:
                ctx.set_error('Failed to delete node', status=400)
                return

            ctx.response = obj.to_dict()
