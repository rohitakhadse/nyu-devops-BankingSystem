# run with:
# nosetests --with-spec --spec-color
# coverage run --omit "venv/*" test_server.py
# coverage report -m --include= server.py

import unittest
import json
import server

# Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409

######################################################################
#  T E S T   C A S E S
######################################################################
class TestBankServer(unittest.TestCase):
    idRef = -1
    # contains one account
    def setUp(self):
        server.app.debug = True
        self.app = server.app.test_client()
        server.connect_to_redis()
        new_account = {'name': 'Gina', 'balance': 1000, 'active': 0}
        data = json.dumps(new_account)
        resp = self.app.post('/accounts', data=data, content_type='application/json')
        self.idRef = json.loads(resp.data)['id']

    def test_index(self):
        resp = self.app.get('/')
        self.assertTrue('Banking System REST API Service' in resp.data)
        self.assertTrue(resp.status_code == HTTP_200_OK)

    def test_create_account_successfully(self):
        new_account = {'name': 'john', 'balance': 100, 'active': 1}
        data = json.dumps(new_account)
        resp = self.app.post('/accounts', data=data, content_type='application/json')
        new_json = json.loads(resp.data)
        # check the return message and return code
        self.assertTrue(resp.status_code == HTTP_201_CREATED )
        self.assertTrue(new_json['name'] == 'john')
        self.assertTrue(new_json['balance'] == '100')
        self.assertTrue(new_json['active'] == '1')

        # check that id has gone up and includes john
        resp = self.app.get('/accounts/%s' %new_json['id'])
        data = json.loads(resp.data)
        self.assertTrue(resp.status_code == HTTP_200_OK)
        self.assertTrue(new_json == data)

    def test_create_account_missing_active_attribute(self):
        new_account = {'name': 'john', 'balance': 100}
        data = json.dumps(new_account)
        resp = self.app.post('/accounts', data=data, content_type='application/json')
        # check the return message and return code
        self.assertTrue(resp.status_code == HTTP_400_BAD_REQUEST)

    def test_create_account_missing_name_attribute(self):
        new_account = {'active': '1', 'balance': 100}
        data = json.dumps(new_account)
        resp = self.app.post('/accounts', data=data, content_type='application/json')
        # check the return message and return code
        self.assertTrue(resp.status_code == HTTP_400_BAD_REQUEST)

    def test_create_account_missing_balance_attribute(self):
        new_account = {'name': 'john', 'active': 1}
        data = json.dumps(new_account)
        resp = self.app.post('/accounts', data=data, content_type='application/json')
        # check the return message and return code
        self.assertTrue(resp.status_code == HTTP_400_BAD_REQUEST)
        
    def test_update_account(self):
    	# Add a user account to later update
    	new_account = {'name' : 'test', 'balance': 511, 'active' :0}
    	data = json.dumps(new_account)
    	resp_add = self.app.post('/accounts', data=data, content_type='application/json')
    	new_json = json.loads(resp_add.data)
    	
    	# Now use the id of the new user to update
    	id = new_json['id']
    	update_account = {'name': 'test', 'balance': 1022}
    	data = json.dumps(update_account)
    	
    	# incomplete data: should return 400_bad_request
    	resp_update_err1 = self.app.put('/accounts/'+id, data=data, content_type='application/json')
    	self.assertTrue(resp_update_err1.status_code == HTTP_400_BAD_REQUEST)
    	update_account = {'name': 'test', 'balance': 1022, 'active': 1}
    	data = json.dumps(update_account)
    	# invalid id
    	resp_update_err2 = self.app.put('/accounts/0', data=data, content_type='application/json')
    	self.assertTrue(resp_update_err2.status_code == HTTP_404_NOT_FOUND)
    	# invalid id 2
    	resp_update_err3 = self.app.put('/accounts/nextId', data=data, content_type='application/json')
    	self.assertTrue(resp_update_err3.status_code == HTTP_404_NOT_FOUND)
    	
    	# Success update
    	resp = self.app.put('/accounts/'+id, data=data, content_type='application/json')
    	self.assertTrue(resp.status_code == HTTP_200_OK)
    	
    	# Clean up
    	self.app.delete('/accounts/'+id, data=data, content_type='application/json')

    def test_get_an_account_by_id(self):
        #first need to create an account to get
        new_account = {'name': 'Hugh Jass', 'balance': 1000, 'active': 0}
        new_account_json = json.dumps(new_account)
        new_account = self.app.post('/accounts', data=new_account_json, content_type='application/json')

        account_id = json.loads(new_account.data)['id']
        account_response = self.app.get('/accounts/' + account_id)
        account_response_json = json.loads(account_response.data)

        self.assertTrue(account_response.status_code == HTTP_200_OK)
        self.assertEquals(account_response_json['name'], 'Hugh Jass')
        self.assertEquals(account_response_json['balance'], '1000')
        self.assertEquals(account_response_json['active'], '0')

    def test_get_an_account_by_id_returns_404_for_invalid_id(self):
        account_response = self.app.get('/accounts/nextId')

        self.assertTrue(account_response.status_code == HTTP_404_NOT_FOUND)

    def test_get_an_account_by_id_returns_404_for_id_that_does_not_exist_yet(self):
        account_id = server.get_next_id()
        account_response = self.app.get('/accounts/' + account_id)

        self.assertTrue(account_response.status_code == HTTP_404_NOT_FOUND)

    def test_get_account_list(self):
        resp = self.app.get('/accounts')
        #print 'resp_data: ' + resp.data
        self.assertTrue( resp.status_code == HTTP_200_OK )
        data = json.loads(resp.data)
        self.assertTrue( len(data) ==  self.get_account_count())
        self.assertFalse( 'nextId' in resp.data)

    def test_get_account_list_with_existing_name(self):
        resp = self.app.get('/accounts?name=Gina')
        #print 'resp_data: ' + resp.data
        self.assertTrue( resp.status_code == HTTP_200_OK )
        for data in json.loads(resp.data):
            self.assertTrue (data['name'] == 'Gina')
        self.assertFalse( 'nextId' in resp.data)

    def test_get_account_list_with_nonexisting_name(self):
        resp = self.app.get('/accounts?name=Xiao')
        #print 'resp_data: ' + resp.data
        self.assertTrue(resp.status_code == HTTP_404_NOT_FOUND)

    def test_get_account_list_with_empty_name(self):
        resp = self.app.get('/accounts?name=')
        #print 'resp_data: ' + resp.data
        self.assertTrue( resp.status_code == HTTP_200_OK )
        data = json.loads(resp.data)
        self.assertTrue( len(data) ==  self.get_account_count())
        self.assertFalse( 'nextId' in resp.data)

    def test_deactivate_a_non_exist_account(self):
        account_response = self.app.put('/accounts/nextId/deactivate')
        print account_response.status_code
        self.assertTrue(account_response.status_code == HTTP_404_NOT_FOUND)

    def test_deactivate_a_valid_account(self):
        #first need to create an account to get
        new_account = {'name': 'Hugh Jass', 'balance': 1000, 'active': 1}
        new_account_json = json.dumps(new_account)
        new_account = self.app.post('/accounts', data=new_account_json, content_type='application/json')

        account_id = json.loads(new_account.data)['id']
        account_response = self.app.put('/accounts/'+account_id+'/deactivate')
        self.assertTrue(account_response.status_code == HTTP_200_OK)

        deactivated_account_response = self.app.get('/accounts/'+account_id)
        data = json.loads(deactivated_account_response.data)
        self.assertTrue(data['active'] == '0')
        
    def test_delete_an_account(self):
        new_account = {'name' : 'Orson Kart', 'balance' : 5000, 'active': 1}
        new_account_json = json.dumps(new_account)
        new_account = self.app.post('/accounts', data=new_account_json, content_type='application/json')

        account_id = json.loads(new_account.data)['id']
        account_delete_response = self.app.delete ('accounts/' + account_id)

        self.assertTrue(account_delete_response.status_code == HTTP_204_NO_CONTENT)
        
        account_get_response = self.app.get('accounts/' + account_id)
        
        self.assertTrue(account_get_response.status_code == HTTP_404_NOT_FOUND)
        
        
    def test_return_204_even_if_no_delete(self):
        account_id = server.get_next_id()
        account_response = self.app.delete('/accounts/' + account_id)

        self.assertTrue(account_response.status_code == HTTP_204_NO_CONTENT)
        

######################################################################
# Utility functions
######################################################################

    def get_account_count(self):
        # save the current number of accounts
        resp = self.app.get('/accounts')
        self.assertTrue( resp.status_code == HTTP_200_OK )
        # print 'resp_data: ' + resp.data
        data = json.loads(resp.data)
        return len(data)

######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
