import datetime
import json

import Business.QuoteConstants as QuoteConstants


class Quote():
    """Class  quotes methods
    """
    @staticmethod
    def quoteToDict(quote,author,tags,borndate=QuoteConstants.NOT_AVAILABLE,city=QuoteConstants.NOT_AVAILABLE,desc=QuoteConstants.NOT_AVAILABLE):
        """Transforms quote´s attributes into dict

        Args:
            quote (str): quote text
            author (str): author´s name
            tags (str): quote´s tags
            borndate (str): date
            city (str): city
            desc (str): description

        Returns:
            dict {}: Quote dictionary
        """
        return {
            "quote": quote,
            "author": author,
            "tags": tags,
            "authorDetails": {
                "borndate" : borndate,
                "city" : city ,
                "desc" : desc
            }
        }

    @staticmethod
    def listToJson(list,exec_name,filename="",rename=False):
        """Transforms list into json

        Args:
            list ([]): quotes dictionary
            exec_name (str): execution time
        """
        if rename == False:
            now = datetime.datetime.now()
            filename = now.strftime("%Y%m%d-%H%M%S")
        with open(f"{exec_name}/{filename}.json", "w",encoding="utf-8") as f:    
                json.dump(list, f, indent=4)
        