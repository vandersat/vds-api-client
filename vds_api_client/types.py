import re
import datetime as dt
from math import ceil
from vds_api_client.requester import Requester

import pandas as pd

REQ = Requester()


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
            raise ValueError(f'Product {item} not found')
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
            return f'{self.api_name}, ({self.name}) [{self.unit}]'
        else:
            return f'{self.api_name} [{self.unit}]'

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
            self._rois = [Roi(id=int(roi_dict.get('id')),
                              name=str(roi_dict.get('name')),
                              area=float(roi_dict.get('area')),
                              description=roi_dict.get('description'),
                              created_at=dt.datetime.strptime(roi_dict.get('created_at'),
                                                              '%Y-%m-%dT%H:%M:%S.%f')
                              if roi_dict.get('created_at') is not None else dt.datetime(1900, 1, 1),
                              display=roi_dict.get('display', None),
                              metadata=roi_dict.get('metadata', None),
                              labels=roi_dict.get('labels', None),
                              geojson=roi_dict.get('geojson', None))
                          for roi_dict in roi_list]
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

    def show_all(self):
        """
        Show all Rois in the viewer, also works on a filtered Roi set

        """
        headers = {'X-Fields': 'rois{id, display}'}
        uri = (f'https://{REQ.host}/api/v2/rois/show-hide-all?'
               f'&ids={",".join([str(roi.id) for roi in self])}')
        rois = REQ.post_content(uri, dict(show=True), headers=headers)['rois']
        for roi in rois:
            try:
                roi_obj = self[int(roi['id'])]
                roi_obj.display = roi['display']
            except ValueError:
                pass

    def hide_all(self):
        """
        Hide all Rois in the viewer, also works on a filtered Roi set

        """
        headers = {'X-Fields': 'rois{id, display}'}
        uri = (f'https://{REQ.host}/api/v2/rois/show-hide-all?'
               f'&ids={",".join([str(roi.id) for roi in self])}')
        rois = REQ.post_content(uri, dict(show=False), headers=headers)['rois']
        for roi in rois:
            try:
                roi_obj = self[int(roi['id'])]
                roi_obj.display = roi['display']
            except ValueError:
                pass

    def filter(self, min_id=None, max_id=None,
               area_min=None, area_max=None,
               name_regex=None,
               description_regex=None,
               created_before=None,
               created_after=None,
               display=None):
        """
        Filter Rois based on these criterea

        Parameters
        ----------
        min_id: int
        max_id: int
        area_min: float
            minimum area in m2
        area_max: float
            maximum area in m2
        name_regex: str
        description_regex: str
        created_before: dt.datetime
        created_after: dt.datetime
        display: bool

        Returns
        -------
        Rois
            filtered roi collection

        """
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
            elif display is not None and roi.display != display:
                continue
            elif created_before is not None and roi.created_at > created_before:
                continue
            elif created_after is not None and roi.created_at < created_after:
                continue
            elif nre is not None and not nre.search(roi.name):
                continue
            elif dre is not None and not dre.search(str(roi.description)):
                continue
            else:
                new_rois.append(roi)
        out = Rois([])
        out._rois = list(new_rois)
        out.filter_applied = True
        return out

    def __str__(self):
        if self.__bool__():
            nlen = max(max([len(r.name) for r in self._rois]), 10)  # max product length display
            prod_ls = [(f' {roi.id:7d}  /  [{"X" if roi.display else " "}]  | {roi.name:{nlen}s} '
                        f'| {roi.area / 1e4 :.3e} ha | {roi.created_at:%Y-%m-%d %H:%M} | {roi.description}')
                       for roi in self._rois]
            body = '\n'.join(prod_ls)
        else:
            nlen = 9
            body = '\tNO ROIS FOUND'
        nwhit = int(ceil((nlen - 8) / 2))
        head = f'\n # ID / DISPLAY # | {"":{nwhit}s}# Name #{"":{nwhit}s} |   # Area #   |  # Created at #  |       # Description #     \n'
        head = head + '=' * len(head) + '\n'
        return head + body

    def __repr__(self):
        return str(self)

    def __len__(self):
        return len(self._rois)

    def __iter__(self):
        return self._rois.__iter__()

    def __getitem__(self, item):
        """
        Return the roi based on the id or name

        Parameters
        ----------
        item: int or str

        Returns
        -------
        Roi

        """
        try:
            if isinstance(item, int):
                pos = self.ids_to_list().index(item)
            else:
                try:
                    pos = [roi.name.lower() for roi in self._rois].index(item.lower())
                except ValueError:
                    pos = self.ids_to_list().index(int(item))
        except ValueError:
            raise ValueError(f'ROI {item} not found')
        return self._rois[pos]

    def ids_to_list(self):
        return [roi.id for roi in self._rois]


class Roi(object):
    """
    Roi object

    Parameters
    ----------
    id: int
        Id of this Roi
    name: str
        Name of this Roi
    area: float
        Area in m2
    description: str
        Description of Roi
    geojson: str, optional
        Geometry as geojson
    display: bool, optional
        Shown in the viewer
    created_at: str, optional
        Datetime string of creation
    metadata: list, optional
        Metadata for this Roi
    labels: list, optional
        Labels applied to this Roi
    geojson: str, optional
        Geojson string

    """
    def __init__(self, id, name, area, description,
                 display=None, created_at=None,
                 metadata=None, labels=None,
                 geojson=None):
        self.id = id
        self.name = name
        self.area = area
        self.description = description
        self.display = display
        self.created_at = created_at
        self.metadata = metadata
        self.labels = labels
        self._geojson = geojson

    def __str__(self):
        return f'roi.id: {self.id}, roi.name: {self.name}\n'

    def __repr__(self):
        return str(self)

    @property
    def uri(self):
        return f'https://{REQ.host}/api/v2/rois/{self.id}'

    @property
    def geojson(self):
        if self._geojson is not None:
            return self._geojson
        else:
            headers = {"X-Fields": 'geojson'}
            self._geojson = REQ.get_content(self.uri, headers=headers)['geojson']
            return self._geojson

    def update(self, name=None, description=None, display=None):
        """
        Update region of interest

        Parameters
        ----------
        name: str, optional
            Rename this roi
        description: str, optional
            Update roi description
        display: bool, optional
            Set display state in the viewer

        """
        headers = {"X-Fields": 'name, description, display'}
        update_dict = {}
        if name is not None:
            update_dict['name'] = name
        if description is not None:
            update_dict['description'] = description
        if display is not None:
            update_dict['display'] = display
        REQ.logger.debug(f'Updating ROI info: {self.uri} with {update_dict}')
        roi = REQ.put_content(self.uri, update_dict, headers=headers)

        # Update self with response
        self.name = roi.get('name')
        self.description = roi.get('description')
        self.display = roi.get('display')

# EOF
