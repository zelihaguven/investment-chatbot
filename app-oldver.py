from flask import Flask, request, jsonify, render_template
import yfinance as yf
from datetime import datetime, timedelta

app = Flask(__name__)

# API URL'leri ve headers kaldırıldı -Yahoo Finance API kullanılıyor

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stocks')
def get_stocks():
    try:
        # Yahoo Finance API'sinden veri çek
        import yfinance as yf
        
        # Borsa İstanbul'daki tüm hisse senedileri
        # Yahoo Finance'ten hisse senedi listesini çek
        def get_all_stocks():
            # BIST 100 endeksinin hisse senedilerini çek
            try:
                # BIST 100 endeksinin hisse senedilerini çek
                stock_list = yf.download(
                    tickers='^BIST100',
                    period='1d',
                    interval='1d'
                )
                
                # Hisse senedilerini al
                stocks = []
                for symbol in stock_list.columns:
                    if symbol.endswith('.IS'):
                        stocks.append(symbol)
                
                return stocks
            except Exception as e:
                print(f"Hisse senedi listesi çekme hatası: {str(e)}")
                # Eğer hata alırsak, varsayılan hisse senedi listesini kullan
                return ['AKBNK.IS', 'GARAN.IS', 'KRDMD.IS', 'TUPRS.IS', 'SAHOL.IS', 
                        'EREGL.IS', 'BIMAS.IS', 'KCHOL.IS', 'SASA.IS', 'TAVHL.IS']
        
        stocks = get_all_stocks()
        
        stock_data = []
        for symbol in stocks:
            try:
                # Hisse senedi bilgilerini çek
                stock = yf.Ticker(symbol)
                info = stock.info
                
                # Verileri formatla
                stock_data.append({
                    'symbol': symbol.replace('.IS', ''),
                    'name': info.get('longName', symbol),
                    'price': float(info.get('regularMarketPrice', 0)),
                    'change': float(info.get('regularMarketChange', 0)),
                    'change_percent': float(info.get('regularMarketChangePercent', 0)),
                    'volume': int(info.get('volume', 0)),
                    'market_cap': float(info.get('marketCap', 0)),
                    'sector': info.get('sector', ''),
                    'industry': info.get('industry', ''),
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            except Exception as e:
                print(f"Hisse senedi ekleme hatası: {str(e)}")
                continue
        
        # Hisse senedileri piyasa değerine göre sırala
        stock_data.sort(key=lambda x: x['market_cap'], reverse=True)
        
        return jsonify({
            'stocks': stock_data,
            'total_stocks': len(stock_data)
        })
    except Exception as e:
        print(f"Hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/<symbol>')
def get_stock_data(symbol):
    try:
        # Yahoo Finance API'sinden veri çek
        stock = yf.Ticker(symbol + '.IS')
        info = stock.info
        
        return jsonify({
            'price': float(info.get('regularMarketPrice', 0)),
            'change': float(info.get('regularMarketChange', 0)),
            'percent_change': float(info.get('regularMarketChangePercent', 0)),
            'volume': int(info.get('volume', 0)),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        print(f"Hisse senedi veri hatası: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/get_investment_advice', methods=['POST'])
def get_investment_advice():
    try:
        data = request.json
        budget = float(data.get('budget', 0))
        investment_period = int(data.get('investment_period', 1))
        risk_level = data.get('risk_level', 'medium')

        if budget <= 0 or investment_period not in [1, 3, 6, 12]:
            return jsonify({'error': 'Geçersiz giriş'}), 400

        # İŞ Yatırım API'si ile hisse senedi analizi
        def analyze_stock(symbol):
            try:
                # 5 günlük veri çek
                stock_data = yf.download(symbol + '.IS', 
                                        start=datetime.now() - timedelta(days=5),
                                        end=datetime.now())
                
                if len(stock_data) == 0:
                    print(f"No data for {symbol}")
                    return None
                
                # Getiri hesapla
                returns = stock_data['Close'].pct_change()
                
                # Risk metrikleri
                volatility = returns.std() * np.sqrt(252)
                sharpe_ratio = returns.mean() / volatility * np.sqrt(252)
                
                # Performans metrikleri
                total_return = (stock_data['Close'][-1] - stock_data['Close'][0]) / stock_data['Close'][0]
                
                # Hisse senedi adını ve diğer bilgileri al
                stock_info = get_stock_data(symbol)
                if stock_info.get('error'):
                    name = symbol
                else:
                    name = stock_info.get('name', symbol)
                
                return {
                    'symbol': symbol,
                    'name': name,
                    'total_return': total_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'last_price': stock_data['Close'][-1],
                    'change': stock_data['Close'][-1] - stock_data['Close'][-2],
                    'volume': stock_data['Volume'][-1]
                }
            except Exception as e:
                print(f"Error analyzing {symbol}: {str(e)}")
                return None

        # Borsa İstanbul'daki popüler hisse senedleri
        stocks_to_analyze = ['AKBNK', 'GARAN', 'KRDMD', 'TUPRS', 'SAHOL', 'EREGL', 'BIMAS', 'KCHOL', 'SASA', 'TAVHL']
        
        # Her hisse senedini analiz et
        stock_analysis = []
        for stock in stocks_to_analyze:
            result = analyze_stock(stock)
            if result:
                stock_analysis.append(result)

        # Eğer hiç hisse senedi analiz edilemezse, varsayılan değer döndür
        if not stock_analysis:
            return jsonify({
                'error': 'Hisse senedi verileri yüklenemedi'
            }), 500

        # Risk seviyesine göre filtrele
        if risk_level == 'low':
            # Düşük risk: Düşük volatilite ve yüksek Sharpe ratio
            best_stock = max(stock_analysis, key=lambda x: x['sharpe_ratio'])
        elif risk_level == 'high':
            # Yüksek risk: Yüksek getiri
            best_stock = max(stock_analysis, key=lambda x: x['total_return'])
        else:
            # Orta risk: Dengeli yaklaşım
            weights = 0.5  # 50% getiri, 50% Sharpe ratio
            best_stock = max(stock_analysis, 
                           key=lambda x: weights * x['total_return'] + (1 - weights) * x['sharpe_ratio'])

        # Döviz analizi
        def analyze_currency(base, target):
            try:
                # 1 yıldan fazla veri çek
                currency_data = yf.download(f'{base}{target}=X', 
                                           start=datetime.now() - timedelta(days=365),
                                           end=datetime.now())
                
                if len(currency_data) == 0:
                    print(f"No data for {base}/{target}")
                    return None
                
                # Getiri hesapla
                returns = currency_data['Close'].pct_change()
                
                # Risk metrikleri
                volatility = returns.std() * np.sqrt(252)
                
                # Performans metrikleri
                total_return = (currency_data['Close'][-1] - currency_data['Close'][0]) / currency_data['Close'][0]
                
                return {
                    'base': base,
                    'target': target,
                    'total_return': total_return,
                    'volatility': volatility
                }
            except Exception as e:
                print(f"Error analyzing {base}/{target}: {str(e)}")
                return None

        # Döviz çiftlerini analiz et
        currency_pairs = [('USD', 'TRY'), ('EUR', 'TRY'), ('GBP', 'TRY')]
        currency_analysis = []
        for base, target in currency_pairs:
            result = analyze_currency(base, target)
            if result:
                currency_analysis.append(result)

        # Eğer hiç döviz çifti analiz edilemezse, varsayılan değer döndür
        if not currency_analysis:
            return jsonify({
                'error': 'Döviz verileri yüklenemedi'
            }), 500

        # En iyi döviz çiftini seç
        best_currency = max(currency_analysis, key=lambda x: x['total_return'])

        # Yatırım önerisi
        analysis = {
            'best_stock': best_stock['symbol'],
            'best_currency': f"{best_currency['base']}/{best_currency['target']}",
            'stock_return': best_stock['total_return'],
            'currency_return': best_currency['total_return'],
            'investment_period': investment_period,
            'budget': budget,
            'risk_level': risk_level,
            'total_profit': budget * (best_stock['total_return'] + best_currency['total_return']) * investment_period / 12,
            'annual_return': (best_stock['total_return'] + best_currency['total_return']) * 100
        }

        return jsonify(analysis)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/currency', methods=['GET'])
def get_currency():
    try:
        # Yahoo Finance API'sinden döviz verilerini çek
        import yfinance as yf
        
        # Döviz çiftleri
        currency_pairs = ['USDTRY=X', 'EURTRY=X', 'GBPTRY=X', 'JPYTRY=X']
        
        currency_rates = {}
        for pair in currency_pairs:
            try:
                # Döviz çiftinin verisini çek
                currency = yf.Ticker(pair)
                info = currency.info
                
                # Para birimini ve kur değerini al
                base_currency = pair[:3]
                target_currency = pair[4:7]
                rate = float(info.get('regularMarketPrice', 0))
                
                currency_rates[pair] = {
                    'base_currency': base_currency,
                    'target_currency': target_currency,
                    'rate': rate,
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            except Exception as e:
                print(f"Döviz kuru çekme hatası ({pair}): {str(e)}")
                continue
        
        return jsonify({
            'rates': currency_rates,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        budget = float(data.get('budget', 0))
        investment_period = int(data.get('investment_period', 1))
        risk_level = data.get('risk_level', 'medium')

        if budget <= 0 or investment_period not in [1, 3, 6, 12]:
            return jsonify({'error': 'Geçersiz giriş'}), 400

        # Tarihsel verileri analiz etmek için
        def analyze_stock(symbol):
            try:
                # 1 yıldan fazla veri çek
                stock_data = yf.download(symbol + '.IS', 
                                        start=datetime.now() - timedelta(days=365),
                                        end=datetime.now())
                
                if len(stock_data) == 0:
                    print(f"No data for {symbol}")
                    return None
                
                # Getiri hesapla
                returns = stock_data['Close'].pct_change()
                
                # Risk metrikleri
                volatility = returns.std() * np.sqrt(252)
                sharpe_ratio = returns.mean() / volatility * np.sqrt(252)
                
                # Performans metrikleri
                total_return = (stock_data['Close'][-1] - stock_data['Close'][0]) / stock_data['Close'][0]
                
                return {
                    'symbol': symbol,
                    'total_return': total_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe_ratio
                }
            except Exception as e:
                print(f"Error analyzing {symbol}: {str(e)}")
                return None

        # Borsa İstanbul'daki popüler hisse senedleri
        stocks_to_analyze = ['AKBNK', 'GARAN', 'KRDMD', 'TUPRS', 'SAHOL', 'EREGL', 'BIMAS', 'KCHOL', 'SASA', 'TAVHL']
        
        # Her hisse senedini analiz et
        stock_analysis = []
        for stock in stocks_to_analyze:
            result = analyze_stock(stock)
            if result:
                stock_analysis.append(result)

        # Eğer hiç hisse senedi analiz edilemezse, varsayılan değer döndür
        if not stock_analysis:
            return jsonify({
                'error': 'Hisse senedi verileri yüklenemedi'
            }), 500

        # Risk seviyesine göre filtrele
        if risk_level == 'low':
            # Düşük risk: Düşük volatilite ve yüksek Sharpe ratio
            best_stock = max(stock_analysis, key=lambda x: x['sharpe_ratio'])
        elif risk_level == 'high':
            # Yüksek risk: Yüksek getiri
            best_stock = max(stock_analysis, key=lambda x: x['total_return'])
        else:
            # Orta risk: Dengeli yaklaşım
            weights = 0.5  # 50% getiri, 50% Sharpe ratio
            best_stock = max(stock_analysis, 
                           key=lambda x: weights * x['total_return'] + (1 - weights) * x['sharpe_ratio'])

        # Döviz analizi
        def analyze_currency(base, target):
            try:
                # 1 yıldan fazla veri çek
                currency_data = yf.download(f'{base}{target}=X', 
                                           start=datetime.now() - timedelta(days=365),
                                           end=datetime.now())
                
                if len(currency_data) == 0:
                    print(f"No data for {base}/{target}")
                    return None
                
                # Getiri hesapla
                returns = currency_data['Close'].pct_change()
                
                # Risk metrikleri
                volatility = returns.std() * np.sqrt(252)
                
                # Performans metrikleri
                total_return = (currency_data['Close'][-1] - currency_data['Close'][0]) / currency_data['Close'][0]
                
                return {
                    'base': base,
                    'target': target,
                    'total_return': total_return,
                    'volatility': volatility
                }
            except Exception as e:
                print(f"Error analyzing {base}/{target}: {str(e)}")
                return None

        # Döviz çiftlerini analiz et
        currency_pairs = [('USD', 'TRY'), ('EUR', 'TRY'), ('GBP', 'TRY')]
        currency_analysis = []
        for base, target in currency_pairs:
            result = analyze_currency(base, target)
            if result:
                currency_analysis.append(result)

        # Eğer hiç döviz çifti analiz edilemezse, varsayılan değer döndür
        if not currency_analysis:
            return jsonify({
                'error': 'Döviz verileri yüklenemedi'
            }), 500

        # En iyi döviz çiftini seç
        best_currency = max(currency_analysis, key=lambda x: x['total_return'])

        # Yatırım önerisi
        analysis = {
            'best_stock': best_stock['symbol'],
            'best_currency': f"{best_currency['base']}/{best_currency['target']}",
            'stock_return': best_stock['total_return'],
            'currency_return': best_currency['total_return'],
            'investment_period': investment_period,
            'budget': budget,
            'risk_level': risk_level,
            'total_profit': budget * (best_stock['total_return'] + best_currency['total_return']) * investment_period / 12,
            'annual_return': (best_stock['total_return'] + best_currency['total_return']) * 100
        }

        return jsonify(analysis)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert_currency', methods=['POST'])
def convert_currency():
    try:
        data = request.json
        amount = float(data.get('amount', 1))
        base_currency = data.get('base_currency', 'USD')
        target_currency = data.get('target_currency', 'TRY')
        
        # Döviz kurlarını al
        currency_data = get_currency()
        if isinstance(currency_data, tuple):
            currency_data = currency_data[0]  # Hata durumunda tuple döner
            
        rates = currency_data.get_json().get('rates', {})
        
        # Döviz çifti için kuru bul
        pair = f"{base_currency}{target_currency}=X"
        rate_info = rates.get(pair)
        if not rate_info:
            return jsonify({'error': 'Döviz çifti bulunamadı'}), 404
            
        # Döviz dönüşümü yap
        rate = rate_info['rate']
        converted_amount = amount * rate
        
        return jsonify({
            'amount': amount,
            'base_currency': base_currency,
            'target_currency': target_currency,
            'rate': rate,
            'converted_amount': converted_amount,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        print(f"Döviz dönüşüm hatası: {str(e)}")
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
