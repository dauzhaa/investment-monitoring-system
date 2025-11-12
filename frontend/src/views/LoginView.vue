<template>
  <v-app>
    <v-main>
      <v-container class="fill-height" fluid>
        <v-row align="center" justify="center">
          <v-col cols="12" sm="8" md="4">
            <v-sheet class="pa-6" rounded="lg" elevation="4">
              <h2 class="text-center mb-4">
                Система Мониторинга Инвестиций
              </h2>

              <v-text-field
                v-model="email"
                label="Email (test@test.ru)"
                variant="outlined"
                @keyup.enter="handleLogin"
              ></v-text-field>
              <v-text-field
                v-model="password"
                label="Пароль (123)"
                type="password"
                variant="outlined"
                @keyup.enter="handleLogin"
              ></v-text-field>

              <v-alert v-if="error" type="error" variant="tonal" class="mb-4">
                {{ error }}
              </v-alert>

              <v-btn
                @click="handleLogin"
                :loading="loading"
                color="primary"
                block
                size="large"
              >
                Войти
              </v-btn>
            </v-sheet>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';

const email = ref('test@test.ru');
const password = ref('123');
const loading = ref(false);
const error = ref(null);

const router = useRouter();

const handleLogin = async () => {
  loading.value = true;
  error.value = null;

  const formData = new URLSearchParams();
  formData.append('username', email.value);
  formData.append('password', password.value);

  try {
    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    localStorage.setItem('token', response.data.access_token);

    router.push('/upload');
  } catch (err) {
    error.value = 'Неверный email или пароль.';
  } finally {
    loading.value = false;
  }
};
</script>