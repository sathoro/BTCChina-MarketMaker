import urllib2, json, time, btcchina, math, sys

class BTCChinaMM(object):
	def __init__(self, public_key, private_key):
		self.btcchina = btcchina.BTCChina(public_key, private_key)

		# minimum trade size
		self.min_btc = .001
		# maximum to be actively trading at one time
		self.max_btc = 10
		
		self.orders = []

		for order in self.btcchina.get_orders()['order']:
			print 'Canceled Order #%s' % order['id']
			self.btcchina.cancel(order['id'])
		
		print 'Setup complete'
		time.sleep(2)

	def trade_spread(self):
		prev_balances = prev_ticker = ''

		while (True):
			if not self.update_balances() or not self.update_prices():
				print 'Can\t reach server!'
				time.sleep(10)
				continue

			balances = 'Balances: %s CNY, %s BTC' % (self.cny, self.btc)
			printed = False

			if prev_balances != balances:
				print balances
				prev_balances = balances
				printed = True

			if self.ticker != prev_ticker:
				print self.ticker
				prev_ticker = self.ticker
				printed = True

			if not printed:
				print '...',
				sys.stdout.flush()
			
			if self.is_buying():
			 	for buy_order in self.get_orders('buy'):
			 		order_response = self.btcchina.get_orders(buy_order['id'], False)
					if order_response is None or 'order' not in order_response or order_response['order']['status'] != 'open':
						self.remove_order(buy_order['id'])
						self.log('filled buy spread: %s' % buy_order['spread'])
						print '>>> BUY order fulfilled!'
			 		if self.ticker['buy'] > buy_order['price']:
						self.cancel_order(buy_order['id'])
			
			if self.is_selling():
				for sell_order in self.get_orders('sell'):
					order_response = self.btcchina.get_orders(sell_order['id'], False)
					if order_response is None or 'order' not in order_response or order_response['order']['status'] != 'open':
						self.remove_order(sell_order['id'])
						self.log('filled sell spread: %s' % sell_order['spread'])
						print '>>> SELL order fulfilled!'
					elif self.ticker['sell'] < sell_order['price']:
						self.cancel_order(sell_order['id'])

			if self.btc > self.min_btc:
				self.new_order('sell')

			if (self.cny / self.ticker['buy']) > self.min_btc:
				self.new_order('buy')

			time.sleep(3)

	def update_prices(self):
		try:
			url = "https://data.btcchina.com/data/orderbook?market=cnybtc"
			response = urllib2.urlopen(url);
			data = json.loads(response.read())
			self.ticker = {
				'buy': float(data['bids'][0][0]),
				'buy_volume': float(data['bids'][0][1]),
				'sell': float(data['asks'][-1][0]),
				'sell_volume': float(data['asks'][-1][1])
			}
			return True
		except:
			return False

	def get_last_trade_price(self):
		try:
			url = "https://data.btcchina.com/data/ticker?market=cnybtc"
			response = urllib2.urlopen(url);
			data = json.loads(response.read())
			return int(float(data['ticker']['last']) * 100)
		except:
			return False

	def get_spread(self):
		return self.ticker['sell'] - self.ticker['buy']

	def new_order(self, type):
		if type == 'buy' or type == 'sell':
			if type == 'buy':
				price = self.get_buy_price()
				amount = math.floor((self.cny / price) * 1000) / 1000
			else:
				price = self.get_sell_price()
				amount = min(self.max_btc, math.floor(self.btc * 1000) / 1000)

			if amount < self.min_btc:
				print 'Amount is too low %s %s' % (type, amount)
				return False
			else:
				if type == 'buy':
					order_id = self.btcchina.buy(price, amount)
				else:
					order_id = self.btcchina.sell(price, amount)

				if order_id is not None and isinstance(order_id, (int, long)):
					print '%sing %s BTC for %s. Order #%s' % (type.title(), amount, price, order_id)
					order = {
						'id': order_id,
						'price': price,
						'amount': amount,
						'type': type,
						'spread': self.get_spread()
					}
					self.orders.append(order)
				else:
					print 'Order has gone very wrong: %s' % order_id
		return False

	def cancel_order(self, order_id):
		if self.btcchina.cancel(order_id) == True:
			print 'Canceled order #%s' % order_id
			self.remove_order(order_id)
			return True
		else:
			print 'Couldn\'t cancel order #%s' % order_id
			return False

	def remove_order(self, order_id):
		self.orders = [x for x in self.orders if not x['id'] == order_id]

	def update_balances(self):
		try:
			account_info = self.btcchina.get_account_info()
			self.btc = float(account_info['balance']['btc']['amount'])
			self.cny = float(account_info['balance']['cny']['amount'])
			return True
		except:
			return False

	def get_orders(self, type):
		orders = [x for x in self.orders if x['type'] == type]
		return orders

	def is_selling(self):
		return len(self.get_orders('sell')) > 0

	def is_buying(self):
		return len(self.get_orders('buy')) > 0

	def get_sell_price(self):
		return self.ticker['sell']

	def get_buy_price(self):
		return self.ticker['buy']

	def log(self, msg):
		f = open('out.txt', 'w')
		f.write(msg + '\n')
		f.close()

def go():
	public_key = ''
	private_key = ''
	bot = BTCChinaMM(public_key, private_key)
	bot.trade_spread()

if __name__ == '__main__':
	go()
