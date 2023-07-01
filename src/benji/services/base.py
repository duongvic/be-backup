from benji.database import Database, Query


class BaseModel(object):
    __model__ = None

    def __init__(self, config=None, init_database: bool = False,
                 migrate_database: bool = False,
                 in_memory_database: bool = False,
                 destroy_database: bool = False):
        self.config = config

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def close() -> None:
        """

        """

    @classmethod
    def get(cls, id):
        return cls.__model__.find_by_id(id)

    @classmethod
    def list(cls):
        return cls.__model__.list()

    @classmethod
    def delete(cls, id, force=False):
        obj = cls.get(id)
        return obj.delete(force)

    @classmethod
    def dump_raw_object(cls, ctx, model, condition):
        data = ctx.data
        page = int(data.pop('page', 1) or 1)
        page_size = int(data.pop('page_size', 10) or 10)

        if not ctx.is_admin():
            if condition:
                condition = '({} and user_id == {})'. \
                    format(condition, ctx.target_user.id) if model.get_model_attr('user_id') else condition
            else:
                condition = '(user_id == {})'.format(ctx.target_user.id) if model.get_model_attr('user_id') else None

        query = Query(model, condition)

        prev_page = None
        raw_data = []
        while True:
            objects = query.paginate(page=page, per_page=page_size, error_out=False)
            raw_data.extend(objects.items)

            if prev_page is None and objects.has_prev:
                prev_page = objects.prev_num

            if raw_data or not objects.has_next:
                break
            page += 1

        return raw_data, objects, prev_page

    @classmethod
    def dump_object(cls, ctx, model, condition=None):
        raw_data, objects, prev_page = cls.dump_raw_object(ctx, model, condition)
        result = []
        if ctx.is_admin:
            for obj in raw_data:
                result.append(obj.to_dict())
        else:
            for obj in raw_data:
                result.append(obj.to_user_dict())

        ctx.response = {
            'data': result,
            'has_more': objects.has_next,
            'next_page': objects.next_num if objects.has_next else None,
            'prev_page': prev_page,
        }
        return result


class BaseService(object):

    def __init__(self, config):
        self._config = config
