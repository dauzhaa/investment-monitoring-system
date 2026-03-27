<template>
  <div class="map-container">
    <div ref="chartRef" class="map-chart"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import * as echarts from 'echarts';
import tyumenGeoJson from '@/assets/tyumen_districts.json';

const props = defineProps({
  data: { type: Array, default: () => [] },
});

const emit = defineEmits(['district-click']);
const router = useRouter(); 

const chartRef = ref(null);
let myChart = null;

const processGeoJson = () => {
  const processed = JSON.parse(JSON.stringify(tyumenGeoJson));
  processed.features.forEach(feature => {
    if (feature.properties.NL_NAME_2) {
      feature.properties.name = feature.properties.NL_NAME_2;
    }
  });
  return processed;
};

const formatMoney = (value) => {
  if (!value || value === 0) return '0 тыс. ₽';
  return new Intl.NumberFormat('ru-RU').format(Math.round(value)) + ' тыс. ₽';
};

const getAggregatedData = () => {
  const geoJson = processGeoJson();
  const aggregated = {};

  (props.data || []).forEach(item => {
    let mappedName = item.name;
    const looseDbName = item.name.replace(/район|г\.|городской округ/gi, '').trim().toLowerCase();
    
    let match = geoJson.features.find(f => {
      const geoName = (f.properties.name || '').replace(/район|г\.|городской округ/gi, '').trim().toLowerCase();
      return geoName === looseDbName;
    });

    if (!match) {
      match = geoJson.features.find(f => {
        const geoName = (f.properties.name || '').replace(/район|г\.|городской округ/gi, '').trim().toLowerCase();
        return geoName.startsWith(looseDbName) || looseDbName.startsWith(geoName);
      });
    }

    if (match) mappedName = match.properties.name;

    if (!aggregated[mappedName]) {
      aggregated[mappedName] = { name: mappedName, originals: [], value: 0 };
    }
    
    aggregated[mappedName].value += (item.value || item.fact || 0);
    if (!aggregated[mappedName].originals.includes(item.name)) {
        aggregated[mappedName].originals.push(item.name);
    }
  });

  return Object.values(aggregated).map(d => ({
    name: d.name,
    originalName: d.originals.join(' + '),
    value: d.value
  }));
};

/* ── Рассчитать пороги visualMap по квантилям ── */
const buildPieces = (mapData) => {
  const values = mapData.map(d => d.value).filter(v => v > 0).sort((a, b) => a - b);
  const colors = ['#B2DFDB', '#80CBC4', '#4DB6AC', '#00897B', '#004D40'];

  if (values.length === 0) {
    return [{ min: 0, max: 1, color: colors[0] }];
  }
  if (values.length < 3) {
    return [{ min: 0, max: Math.max(...values) + 1, color: colors[2] }];
  }

  // Квантили: 20 / 40 / 60 / 80 — дают 5 корзин
  const quantile = (arr, q) => arr[Math.min(Math.floor(arr.length * q), arr.length - 1)];
  const raw = [0, quantile(values, 0.2), quantile(values, 0.4), quantile(values, 0.6), quantile(values, 0.8), values[values.length - 1] + 1];

  // Убрать дубликаты (если данные очень однородные)
  const thresholds = [...new Set(raw)].sort((a, b) => a - b);

  const pieces = [];
  for (let i = 0; i < thresholds.length - 1; i++) {
    pieces.push({
      min: thresholds[i],
      max: thresholds[i + 1] - (i < thresholds.length - 2 ? 0.01 : 0),
      color: colors[Math.min(i, colors.length - 1)]
    });
  }
  return pieces;
};

const initChart = () => {
  if (!chartRef.value) return;

  const geoJson = processGeoJson();
  echarts.registerMap('TYUMEN', geoJson);
  myChart = echarts.init(chartRef.value);

  const mapData = getAggregatedData();

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#1D9E75',
      borderWidth: 1,
      textStyle: { color: '#1B3A5C' },
      formatter: (params) => {
        const displayName = params.data?.originalName || params.name;
        const value = params.value || 0;
        return `<div style="padding: 8px;">
          <div style="font-size: 15px; font-weight: bold; margin-bottom: 4px;">${displayName}</div>
          <div style="color: #2E7D32; font-weight: 600; font-size: 14px;">Факт: ${formatMoney(value)}</div>
          <div style="color: #757575; font-size: 11px; margin-top: 6px;">Нажмите для просмотра карточки</div>
        </div>`;
      }
    },
    visualMap: {
      type: 'piecewise',
      pieces: buildPieces(mapData),
      text: ['Высокие', 'Низкие'],
      orient: 'vertical',
      left: 20,
      bottom: 20,
      itemWidth: 16,
      itemHeight: 16,
      outOfRange: { color: '#E8E8E8' },
      textStyle: { color: '#1B3A5C', fontWeight: 'bold' }
    },
    series: [{
      name: 'Инвестиции', 
      type: 'map', 
      map: 'TYUMEN', 
      roam: false,
      zoom: 1.15, 
      center: [68.5, 57.5],
      aspectScale: 0.85, 
      nameProperty: 'name', 
      selectedMode: 'single', 
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 12, fontWeight: 'bold', color: '#fff', formatter: (p) => p.data?.originalName || p.name },
        itemStyle: { areaColor: '#F57C00', borderColor: '#fff', borderWidth: 2 }
      },
      select: {
        label: { show: true, fontSize: 12, fontWeight: 'bold', color: '#fff', formatter: (p) => p.data?.originalName || p.name },
        itemStyle: { areaColor: '#F57C00', borderColor: '#fff', borderWidth: 2 }
      },
      itemStyle: { 
        areaColor: '#E8E8E8', 
        borderColor: '#FFFFFF', 
        borderWidth: 1.5,
        shadowColor: 'rgba(27, 58, 92, 0.25)',
        shadowBlur: 8,
        shadowOffsetY: 4
      },
      data: mapData
    }]
  };

  myChart.setOption(option);

  myChart.on('click', (params) => {
    const actualName = params.data?.originalName ? params.data.originalName.split(' + ')[0] : params.name;
    if (params.componentType === 'series' && actualName) {
      emit('district-click', actualName);
      router.push({ name: 'DistrictDetail', params: { name: actualName } });
    }
  });

  window.addEventListener('resize', handleResize);
};

const handleResize = () => { if (myChart) myChart.resize(); };

const updateData = () => {
  if (myChart && props.data) {
    const mapData = getAggregatedData();
    myChart.setOption({
      visualMap: { pieces: buildPieces(mapData) },
      series: [{ data: mapData }]
    });
  }
};

watch(() => props.data, () => nextTick(updateData), { deep: true });
onMounted(() => nextTick(initChart));
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if (myChart) { myChart.off('click'); myChart.dispose(); myChart = null; }
});
</script>

<style scoped>
.map-container { width: 100%; height: 100%; position: relative; }
.map-chart { width: 100%; height: 100%; min-height: 450px; }
</style>