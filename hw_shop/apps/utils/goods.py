def get_breadcrumb(category):
    '''
    接收最低级别的类别, 获取各个类别的名称, 返回
    '''

    dict = {
        'cat1': '',
        'cat2': '',

    }

    if category.parent is None:
        dict['cat1'] = category.name
    elif category.parent.parent is None:
        dict['cat2'] = category.name
        dict['cat1'] = category.parent.name

    return dict
