from django.core.paginator import Paginator as Paginator, PageNotAnInteger, EmptyPage


PAGE_SIZE = 40


class AreaPaginator(Paginator):
    def __init__(self, object_list):
        super(AreaPaginator, self).__init__(object_list=object_list, per_page=PAGE_SIZE, orphans=30)

    def get_page(self, number):
        """
        Return a valid page, even if the page argument isn't a number or isn't
        in range.
        """
        try:
            number = self.validate_number(number)
        except PageNotAnInteger:
            number = self.num_pages  # unlike default django behavior we want to go to the last page by default
        except EmptyPage:
            number = self.num_pages
        return self.page(number)
