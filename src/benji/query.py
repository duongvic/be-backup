
def query(model_class, *args, order_by=None, **kwargs):
    """
    Create query for model class. E.g.
        products = query(md.Product, order_by=md.Product.create_date.desc(),
                         type=<product type>, status='ENABLED').all()
    :param model_class:
    :param args:
    :param order_by:
    :param kwargs:
    :return:
    """
    qry = model_class.query
    for cond in args:
        qry = qry.filter(cond)
    for k, v in kwargs.items():
        qry = qry.filter(getattr(model_class, k) == v)

    if order_by is not None:
        if isinstance(order_by, list):
            qry = qry.order_by(*order_by)
        else:
            qry = qry.order_by(order_by)

    return qry


def paginate(model_class, *args, page=1, page_size=10, error_out=False,
             order_by=None, **kwargs):
    """
    List model objects as pages.
    :param model_class:
    :param args:
    :param page:
    :param page_size:
    :param error_out:
    :param order_by:
    :param kwargs:
    :return:
    """
    q = query(model_class, *args, order_by=order_by, **kwargs)
    return q.paginate(page=page, per_page=page_size, error_out=error_out)
    # Items: result.items
    # Next page: result.has_next, result.next_num
    # Prev page: result.has_prev, result.prev_num


def iterate(model_class, *args, page_size=10, order_by=None, **kwargs):
    """
    Iter objects by page.
    In case we need to iterate over a large number of object, use this.
    Do not use query().all() as it may cause overflow error.
    """
    q = query(model_class, *args, order_by=order_by, **kwargs)
    page = 1
    while True:
        paginating = q.paginate(page=page, per_page=page_size, error_out=False)
        for item in paginating.items:
            yield item
        if paginating.has_next:
            page = paginating.next_num
        else:
            break
