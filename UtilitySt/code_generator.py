from jinja2 import Template


class CodeGenerator(object):

    def __init__(self, select_distribution, scale, loc, a, name,):


    def cod_plot(self):
        """
        Для генерации кода я передаю: {loc} и {scale}, которые будут иметь свое имя и значения,
        и {a}, которые будут параметрами формы - их может быть много, и каждый будет напечатан в
        новой строке {select_distribution} - передается из ползунка {name} содержит только название
        параметров формы, без значений. Должен размещаться без отступа, иначе код py будет с отступом
        :return:
        """

