import time


class CodeGenerator(object):
    """
    Для генерации кода я передаю: {loc} и {scale}, которые будут иметь свое имя и значения,
    и {a}, которые будут параметрами формы - их может быть много, и каждый будет напечатан в
    новой строке {select_distribution} - передается из ползунка {имя} содержит только название
    параметров формы, без значений. Должен размещаться без отступа, иначе код py будет с отступом
    """
    def __init__(self, select_distribution, scale, loc, a, name):
        self.select_distribution = select_distribution
        self.scale = scale
        self.loc = loc
        self.name = name
        self.a = a

    def get_generated_code(self):

        generate_code = f"""
        # -*- coding: utf-8 -*-
        # {time.strftime("%Y%m%d_%H%M%S")}
        # ---
        
        import matplotlib.pyplot as plt #v3.2.2
        import numpy as np #v1.18.5
        from scipy.stats import {self.select_distribution} #v1.6.1
        
        # Set random seed
        np.random.seed(1)
        
        # Function parameters
        {self.scale}
        {self.loc}
        {self.a}              
        
        # Генерировать равномерно числа в течение указанного интервала
        size = 400
        x = np.linspace({self.select_distribution}.ppf(0.001, {self.name} loc=loc, scale=scale ), 
                        {self.select_distribution}.ppf(0.999, {self.name} loc=loc, scale=scale ),
                        size)
        
        # Freeze the distribution
        rv = {self.select_distribution}({self.name} loc=loc, scale=scale)
        
        # Generate random numbers
        r = {self.select_distribution}.rvs({self.name} loc=loc, scale=scale, size=size)
        
        # Make a plot
        fig, ax = plt.subplots(2, 1,
                               gridspec_kw={{'height_ratios': [9, 0.7]}})
        
        # Plot PDF, CDF and SF
        ax[0].plot(x, rv.pdf(x), linestyle='-', color='#3182bd', lw=3, label='PDF')
        ax[0].plot(x, rv.cdf(x), linestyle='-', color='k', lw=3, label='CDF')
        ax[0].plot(x, rv.sf(x), linestyle='-', color='#df65b0', lw=3, label='SF')
        
        # Plot Histogram
        ax[0].hist(r, density=True, bins=20, color='lightgrey',
                   edgecolor='k', label='Sample')
        
        # Plot Boxplot
        bp = ax[1].boxplot(r, patch_artist=True,
                   vert=False,
                   notch=False,
                   showfliers=False,
                   ) 
        # Boxplot aestetic
        for median in bp['medians']: median.set(color ='red', linewidth = 2) 
        for patch in bp['boxes']: patch.set(facecolor='white') 
        
        # Set legend
        ax[0].legend(bbox_to_anchor=(0,1.1,1,0.2), 
                     loc="center", 
                     borderaxespad=0, ncol=2)
        
        # Set Figure aestetics
        ax[0].spines['top'].set_visible(False)
        ax[0].spines['right'].set_visible(False)
        ax[0].set_title('Distribution: {self.select_distribution}')
        
        ax[1].set_xlim(ax[0].get_xlim())
        ax[1].set_ylim(0.9, 1.1)
        ax[1].spines['left'].set_visible(False)
        ax[1].spines['top'].set_visible(False)
        ax[1].spines['right'].set_visible(False)
        ax[1].set_yticklabels([])
        ax[1].set_yticks([])
        
        ax[1].set_xlabel('X value')
        ax[0].set_ylabel('Density')
        
        plt.show()
        
        """
        return generate_code
