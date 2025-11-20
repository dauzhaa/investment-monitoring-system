<template>
  <v-container class="fill-height bg-grey-lighten-4" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-4 pa-4 rounded-lg">
          <div class="text-center mb-4 mt-2">
             <v-avatar color="primary" size="64" class="mb-2">
               <v-icon icon="mdi-chart-line" size="32" color="white"></v-icon>
             </v-avatar>
             <h2 class="text-h5 font-weight-bold text-primary">InvestMonitor72</h2>
             <div class="text-caption text-grey">Вход в систему</div>
          </div>

          <v-card-text>
            <v-form @submit.prevent="handleLogin">
              <v-text-field
                v-model="email"
                label="Email / Логин"
                prepend-inner-icon="mdi-email-outline"
                variant="outlined"
                density="comfortable"
                color="primary"
              ></v-text-field>

              <v-text-field
                v-model="password"
                label="Пароль"
                prepend-inner-icon="mdi-lock-outline"
                type="password"
                variant="outlined"
                density="comfortable"
                color="primary"
                class="mt-2"
              ></v-text-field>

              <v-btn
                type="submit"
                block
                color="primary"
                size="large"
                class="mt-4 font-weight-bold"
                :loading="loading"
              >
                Войти
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
        <div class="text-center mt-4 text-grey text-caption">
          © 2025 Департамент образования и науки ТО
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const email = ref('');
const password = ref('');
const loading = ref(false);
const router = useRouter();

const handleLogin = async () => {
  loading.value = true;
  try {
    const formData = new FormData();
    formData.append('username', email.value);
    formData.append('password', password.value);

    const response = await axios.post('/api/v1/auth/token', formData);
    localStorage.setItem('token', response.data.access_token);
    router.push('/dashboard');
  } catch (error) {
    alert('Ошибка входа! Проверьте пароль.');
  } finally {
    loading.value = false;
  }
};
</script>