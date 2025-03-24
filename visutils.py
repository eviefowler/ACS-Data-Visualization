import cartopy.crs as ccrs
import cartopy.feature
import cartopy.io.shapereader as shpreader
from cartopy.feature import ShapelyFeature
import numpy as np
import pandas as pd
from matplotlib import colormaps, pyplot as plt

def pie(df, grouper, **kwargs):
    grpd = df.reset_index()[['index', grouper]].groupby(grouper).count()
    
    fig, ax = plt.subplots(**kwargs)
    w, t, a = ax.pie(grpd['index'], autopct = lambda pct: f'{round(pct, 1)}%')
    ax.legend(w, grpd.index, bbox_to_anchor = (1, 1), loc = 'upper left')
    plt.show()
    
def singleBar(df, grouper, value
              , xlab = None, ylab = None, yl = None, sortvalues = False
              , **kwargs
             ):
    grpd = df.groupby([grouper])[[value]].mean()
    if sortvalues:
        grpd = grpd.sort_values(value)
    
    fig, ax = plt.subplots(**kwargs)
    ax.bar(grpd.index, grpd[value])
    ax.set_xlabel(xlab if xlab else grouper)
    ax.set_ylabel(ylab if ylab else value)
    if yl:
        ax.set_ylim(yl)
    plt.show()
    
def groupedBar(df, category, grouper, value, function = 'mean'
               , xlab = None, ylab = None, yl = None, sortvalues = False
               , **kwargs
              ):
    grpd = df.groupby([grouper, category])[[value]].agg(function)
        
    xlabs = grpd.index.levels[1]
    xticks = np.arange(len(xlabs))
    cats = grpd.index.levels[0]
    
    if sortvalues:
        grpd = grpd.sort_values(by = value)
        tgtIndex = grpd.loc[cats[0]].index
        grpd = pd.concat([(grpd
                            .loc[cat]
                            .loc[tgtIndex]
                            .assign(temp = cat)
                            .rename(columns = {'temp': grouper})
                            .reset_index()
                            .set_index([grouper, category])) for cat in cats])
        xlabs = tgtIndex
        
    width = 0.9 / len(cats)

    fig, ax = plt.subplots(**kwargs)

    for i, cat in enumerate(cats):
        for lab in [lab for lab in xlabs if lab not in grpd.loc[cat].index]:
            grpd.loc[(cat, lab), value] = None
        rects = ax.bar(xticks + (i * width), grpd.loc[cat].loc[xlabs, value], width = width, label = cat)

    ax.set_xticks((xticks * 2 + len(cats) * width - width) / 2, xlabs)
    ax.set_xlabel(xlab if xlab else category)
    ax.set_ylabel(ylab if ylab else value)
    if yl:
        ax.set_ylim(yl)
    ax.legend()
    plt.show()
    
def stackedBar(df, category, grouper, value, function = 'count'
               , xlab = None, ylab = None, yl = None, sortvalues = False, scale = False
               , **kwargs):
    grpd = df.groupby([grouper, category])[[value]].agg(function)
    
    if scale:
        grpd = pd.merge(grpd.reset_index()
                        , grpd.reset_index().groupby(category)[[value]].sum().rename(columns = {value: 'Category Level'})
                        , how = 'outer', on = category
                       )
        grpd[value] = grpd[value] / grpd['Category Level']
        grpd = grpd.drop(columns = ['Category Level']).sort_values([grouper, category]).set_index([grouper_category])
        
    if sortvalues:
        grpd = grpd.sort_values(by = value)
        tgtIndex = grpd.loc[cats[0]].index
        grpd = pd.concat([(grpd
                            .loc[cat]
                            .loc[tgtIndex]
                            .assign(temp = cat)
                            .rename(columns = {'temp': grouper})
                            .reset_index()
                            .set_index([grouper, category])) for cat in cats])

    fig, ax = plt.subplots()
    bottom = [0 for lvl in grpd.index.levels[1]]
    for grpr in grpd.index.levels[0]:
        ht = grpd.loc[grpr, 'Count']
        p = ax.bar(ht.index, ht, 0.9, label = grpr, bottom = bottom)
        bottom += ht
        
    ax.set_xlabel(xlab if xlab else category)
    ax.set_ylabel(ylab if ylab else value)
    if yl:
        ax.set_ylim(yl)
    ax.legend()
    plt.show()
    
def createStateMap(stl, colorFeature, zoom = [-170, -50, 15, 75], colormap = 'PiYG'):
    # create a scaled color feature
    stl['Scaled'] = (stl[colorFeature] - stl[colorFeature].min()) / (stl[colorFeature].max() - stl[colorFeature].min())
    
    # create a map
    fig = plt.figure(figsize = (10, 5))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    
    # default zoom: North America
    ax.set_extent(zoom, crs=ccrs.PlateCarree())
    
    # load state shapes
    states_shp = shpreader.natural_earth(resolution = '110m', category = 'cultural', name = 'admin_1_states_provinces')
    states = shpreader.Reader(states_shp)
    
    # standard color map: diverging
    nps = colormaps[colormap]
    
    # iterate through states, coloring by desired feature
    for state in states.records():
        st = ShapelyFeature([state.geometry]
                            , ccrs.PlateCarree()
                            , facecolor = nps(stl.loc[state.attributes['name'], 'Scaled'])
                            , alpha = 0.5
                            , edgecolor = 'black')
        ax.add_feature(st)
        
    # add map features
    ax.coastlines()
    ax.add_feature(cartopy.feature.STATES)
    ax.add_feature(cartopy.feature.LAKES)
    ax.add_feature(cartopy.feature.OCEAN)
    ax.add_feature(cartopy.feature.RIVERS)
    ax.add_feature(cartopy.feature.LAND)

    plt.imshow([[stl[colorFeature].min()], [stl[colorFeature].max()]], origin = 'lower', cmap = colormap, interpolation = 'nearest')
    plt.colorbar(location = 'bottom', shrink = 0.5)
    plt.show()