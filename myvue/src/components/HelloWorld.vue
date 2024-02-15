

<template>
  <div id="app">
    <form @submit.prevent="sendData">
      <label for="type">type:</label>
      <input type="text" id="type" v-model="type" required><br><br>

      <label for="coina">Coin A:</label>
      <input type="text" id="coina" v-model="coina" required><br><br>

      <label for="coinb">Coin B:</label>
      <input type="text" id="coinb" v-model="coinb" required><br><br>

      <label for="amount">Amount:</label>
      <input type="text" id="amount" v-model="amount" required @input="validateAmount"><br><br>

      <button type="submit">Submit</button>
    </form>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  data() {
    return {
      type: '',
      coina: '',
      coinb: '',
      amount: ''
    };
  },
  methods: {
    sendData() {
      if (!this.isValidAmount()) {
        alert("Invalid amount: must be a number with up to 18 decimal places.");
        return;
      }
      

      
      const dataToSend = {
        type: this.type,
        coina: this.coina,
        coinb: this.coinb,
        amount: this.amount,
      };


      for(let i = 0; i < 1; i++){
        axios.post('http://127.0.0.1:8000/process_swap', dataToSend)
        .then(result => {
          console.log("Parsed result:", result.data); // 查看解析后的结果
          })
      }
    },
    validateAmount() {
      this.amount = this.amount.replace(/[^0-9.]/g, '').replace(/(\..*)\./g, '$1');
    },
    isValidAmount() {
      return /^(\d+(\.\d{0,18})?)?$/.test(this.amount);
    },
    
  },
};
</script>

<style scoped>
/* 可选的样式 */
</style>


<!--
<template>
  <div id="app">
    <form @submit.prevent="sendData">
      <label for="website">website:</label>
      <input type="text" id="website" v-model="website" required><br><br>

      <label for="coina">Coin A:</label>
      <input type="text" id="coina" v-model="coina" required><br><br>

      <label for="coinb">Coin B:</label>
      <input type="text" id="coinb" v-model="coinb" required><br><br>

      <label for="amount">Amount:</label>
      <input type="text" id="amount" v-model="amount" required @input="validateAmount"><br><br>

      <button type="submit">Submit</button>
    </form>
  </div>
</template>

<script>
export default {
  data() {
    return {
      website: '',
      coina: '',
      coinb: '',
      amount: ''
    };
  },
  methods: {
    sendData() {
      if (!this.isValidAmount()) {
        alert("Invalid amount: must be a number with up to 18 decimal places.");
        return;
      }
      const dataToSend = {
        website: this.website,
        coina: this.coina,
        coinb: this.coinb,
        amount: this.amount
      };

      fetch('http://127.0.0.1:8000/process-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataToSend),
      })
      .then(response => {
        if (response.ok) {
          return response.text();
        } else {
          throw new Error('Failed to send data');
        }
      })
      .then(data => {
        console.log(data);
      })
      .catch(error => {
        console.error('Error:', error);
      });
    },
    validateAmount() {
      this.amount = this.amount.replace(/[^0-9.]/g, '').replace(/(\..*)\./g, '$1');
    },
    isValidAmount() {
      return /^(\d+(\.\d{0,18})?)?$/.test(this.amount);
    }
  }
};
</script>

<style scoped>
/* 可选的样式 */
</style>

-->