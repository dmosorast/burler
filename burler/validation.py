"""
Set of validation methods to assert some consistencies with Singer-related items.

Furute Work: Figure out how to use this to instrument singer.write_record(), etc.

e.g., that a bookmark doesn't ever go backwards
"""

import singer

# Not sure if this is the right pattern, but I wrote thiscode for
# debugging, and it seems useful to expand on
class BookmarkMonitor():
    def __init__(self):
        self.sorting_map = []
        self.last_bookmark = None
        self.last_ordering = None
        self.count = 0

    # TODO: Would be great to have a callback that's called on change in ordering.
    # Perhaps with a map of data.
    # - E.g., callback(old_order, new_order, old_order_length, last_bookmark, current_bookmark, record)
    def track_bookmark_order(self, record, replication_key):
        """ Apply bookmark order tracking, generate sorting_map of changes in sort order. """
        parsed_bm = singer.utils.strptime_to_utc(record[replication_key])
        def switch_event(new_order):
            if self.last_ordering:
                self.sorting_map.append([self.last_ordering, self.count])
            self.count = 0
            self.last_ordering = new_order

        if self.last_bookmark and self.last_bookmark < parsed_bm:
            if self.last_ordering != 'ASC':
                switch_event('ASC')
        elif self.last_bookmark and self.last_bookmark > parsed_bm:
            if self.last_ordering != 'DESC':
                switch_event('DESC')
        elif self.last_bookmark and self.last_bookmark == parsed_bm:
            if self.last_ordering != 'EQUAL':
                switch_event('EQUAL')
        self.count += 1
        self.last_bookmark = parsed_bm

# Original Code:
                # parsed_bm = singer.utils.strptime_to_utc(record['ActivityDate'])
                # global last_sorting_map
                # global last_bookmark
                # global last_ordering
                # global count
                # if last_bookmark and last_bookmark < parsed_bm:
                #     if last_ordering != 'ASC':
                #         sorting_map.append([last_ordering, count])
                #         count = 1
                #         last_ordering = 'ASC'
                #     else:
                #         count += 1
                # elif last_bookmark and last_bookmark > parsed_bm:
                #     if last_ordering != 'DESC':
                #         sorting_map.append([last_ordering, count])
                #         count = 1
                #         last_ordering = 'DESC'
                #     else:
                #         count += 1
                # elif last_bookmark and last_bookmark == parsed_bm:
                #     if last_ordering != 'EQUAL':
                #         sorting_map.append([last_ordering, count])
                #         count = 1
                #         last_ordering = 'EQUAL'
                #     else:
                #         count += 1

                # last_bookmark = parsed_bm
