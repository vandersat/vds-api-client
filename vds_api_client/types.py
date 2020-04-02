import re
from math import ceil


class Products(object):
    """
    Collection of products

    Parameters
    ----------
    product_dict: dict or None
        Product dictionary loaded from
    """
    def __init__(self, product_dict):
        if product_dict is None:
            self._products = {}
        else:
            self._products = [Product(**product_item)
                              for product_item
                              in product_dict]
            self._products.sort(key=lambda x: x.api_name)

    def __bool__(self):
        empty = len(self._products) == 0
        return not empty

    def __contains__(self, item):
        try:
            self.__getitem__(item)
            return True
        except ValueError:
            return False

    def __str__(self):
        return str(self._products)

    def __repr__(self):
        return str(self)

    def __len__(self):
        return len(self._products)

    def __iter__(self):
        """
        Iterate over products

        Yiels
        -----
        product: Product
        """
        return self._products.__iter__()

    def __getitem__(self, item):
        if type(item) is int:
            return self._products[item]
        else:
            found = [product for product in self._products
                     if (product.api_name.lower() == item.lower()
                         or product.name.lower() == item.lower())]
        if not found:
            raise ValueError('Product {} not found'.format(item))
        return found[0]


class Product(object):
    """
    Single api product
    """
    def __init__(self, api_name=None, name=None, abbreviation=None, area_allowed=None,
                 default_legend_id=None, groups=None, max_val=None, min_val=None,
                 time_series_type=None, max_zoom=None, unit='-', **kwargs):
        self.api_name = api_name
        self.name = name
        self.abbreviation = abbreviation
        self.area_allowed = area_allowed
        self.default_legend_id = default_legend_id
        self.groups = groups
        self.max_val = max_val
        self.min_val = min_val
        self.time_series_type = time_series_type
        self.unit = unit
        self.max_zoom = max_zoom
        self.kwargs = kwargs

    def __str__(self):
        if self.api_name != self.name:
            return '{}, ({}) [{}]'.format(self.api_name, self.name, self.unit)
        else:
            return '{} [{}]'.format(self.api_name, self.unit)

    def __repr__(self):
        return str(self)


class Rois(object):
    """
    roi_list: list or None
    """
    def __init__(self, roi_list):

        if roi_list is None:
            self._rois = ()
        else:
            self._rois = tuple(Roi(id=int(roi_dict['id']),
                                   name=str(roi_dict['name']),
                                   area=roi_dict['area'],
                                   description=str(roi_dict['description']))
                               for roi_dict in roi_list)
        self.filter_applied = False

    def __bool__(self):
        empty = len(self._rois) == 0
        return not empty

    def __contains__(self, item):
        try:
            self.__getitem__(item)
            return True
        except ValueError:
            return False

    def filter(self, min_id=None, max_id=None,
               area_min=None, area_max=None,
               name_regex=None,
               description_regex=None):
        new_rois = []
        nre = re.compile(name_regex) if name_regex else None
        dre = re.compile(description_regex) if description_regex else None
        for roi in self:
            if min_id is not None and roi.id < min_id:
                continue
            elif max_id is not None and roi.id > max_id:
                continue
            elif area_min is not None and roi.area < area_min:
                continue
            elif area_max is not None and roi.area > area_max:
                continue
            elif area_min is not None and roi.area < area_min:
                continue
            elif nre is not None and not nre.search(roi.name):
                continue
            elif dre is not None and not dre.search(roi.description):
                continue
            else:
                new_rois.append(roi)
        out = Rois([])
        out._rois = tuple(new_rois)
        out.filter_applied = True
        return out

    def __str__(self):
        if self.__bool__():
            nlen = max(max([len(r.name) for r in self._rois]), 10)  # max product length display
            prod_ls = [(' {:6d} | {:'+str(nlen)+'s} | {:.3e} ha | {}').format(roi.id,
                                                                              roi.name,
                                                                              roi.area / 10000,
                                                                              roi.description)
                       for roi in self._rois]
            body = '\n'.join(prod_ls)
        else:
            nlen = 9
            body = '\tNO ROIS FOUND'
        head = '\n # ID # | {}# Name #{} |   # Area #   |       # Description #     \n'.format(
            ' ' * int(ceil((nlen - 8) / 2.0)), ' ' * int(ceil((nlen - 8) / 2.0)))
        head = head + '=' * len(head) + '\n'
        return head + body

    def __repr__(self):
        return str(self)

    def __len__(self):
        return len(self._rois)

    def __iter__(self):
        return self._rois.__iter__()

    def __getitem__(self, item):
        if type(item) is int:
            found = [roi.id for roi in self._rois if roi.id == item]
        else:
            found = [roi.id for roi in self._rois if roi.name.lower() == item.lower()]
            if not found:
                try:
                    found = [roi.id for roi in self._rois if roi.id == int(item)]
                except ValueError:
                    found = []
        if not found:
            raise ValueError('ROI {} not found'.format(item))
        return found[0]

    def ids_to_list(self):
        return [roi.id for roi in self._rois]


class Roi(object):
    """
    Roi object

    Parameters
    ----------
    id: int
    name: str
    area: float
    description: str
    """
    def __init__(self, id, name, area, description, geometry=None):
        self.id = id
        self.name = name
        self.area = area
        self.description = description
        self.geometry = geometry

    def __str__(self):
        return 'roi.id: {}, roi.name: {}\n'.format(self.id, self.name)

    def __repr__(self):
        return str(self)

# EOF
