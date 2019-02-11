from django.core.paginator import Paginator as Paginator, PageNotAnInteger, EmptyPage


class AreaPaginator(Paginator):
    def get_page(self, number):
        """
        Return a valid page, even if the page argument isn't a number or isn't
        in range.
        """
        try:
            number = self.validate_number(number)
        except PageNotAnInteger:
            number = self.num_pages
        except EmptyPage:
            number = self.num_pages
        return self.page(number)
